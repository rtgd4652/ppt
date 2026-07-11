const DEFAULT_API_ENDPOINT = "https://f7d.huijiwiki.com/api.php";

class WikiClient {
  constructor(browser, options = {}) {
    if (!browser) {
      throw new Error("WikiClient 需要传入 BrowserManager 实例。");
    }

    this.browser = browser;
    this.apiEndpoint = options.apiEndpoint || DEFAULT_API_ENDPOINT;
  }

  // 封装 MediaWiki API 请求。Collector 不允许直接拼 API，必须走这里。
  async request(params) {
    const url = this.#buildApiUrl(params);
    const result = await this.browser.download(url, null, {
      headers: {
        accept: "application/json,text/plain,*/*",
      },
      throwOnError: false,
    });

    const text = result.buffer.toString("utf8");
    if (result.status !== 200 || !text.trim().startsWith("{")) {
      throw new Error(
        [
          "MediaWiki API 未返回 JSON。",
          `HTTP：${result.status}`,
          `Content-Type：${result.headers["content-type"] || "unknown"}`,
          `Preview：${text.slice(0, 300)}`,
        ].join("\n")
      );
    }

    return JSON.parse(text);
  }

  // 获取单页完整信息：页面基础信息、分类、解析后的 HTML、链接和页面引用图片名。
  async get_page(title) {
    const info = await this.request({
      action: "query",
      prop: "info|categories",
      titles: title,
      cllimit: "500",
      redirects: "1",
    });

    const page = info.query?.pages?.[0];
    if (!page || page.missing) {
      throw new Error(`页面不存在：${title}`);
    }

    const parsed = await this.request({
      action: "parse",
      page: page.title,
      prop: "text|images|categories|links|displaytitle|sections",
      redirects: "1",
      disableeditsection: "1",
    });

    const parse = parsed.parse;

    return {
      title: parse.title || page.title,
      displayTitle: parse.displaytitle || parse.title || page.title,
      pageid: page.pageid,
      touched: page.touched,
      sourceUrl: `https://f7d.huijiwiki.com/wiki/${encodeURIComponent(page.title).replace(/%20/g, "_")}`,
      categories: (page.categories || []).map((item) => item.title.replace(/^分类:/, "")),
      html: parse.text || "",
      imageNames: parse.images || [],
      links: parse.links || [],
      sections: parse.sections || [],
      raw: {
        info,
        parsed,
      },
    };
  }

  // 搜索页面。第一版只作为调试/人工定位入口，不用于全站同步。
  async search(keyword, limit = 10) {
    const response = await this.request({
      action: "query",
      list: "search",
      srsearch: keyword,
      srlimit: String(limit),
    });

    return response.query?.search || [];
  }

  // 获取某个分类的成员。第一版只提供能力，不在 Collector 中做批量分类同步。
  async get_category_members(category, limit = 50) {
    const title = category.startsWith("分类:") ? category : `分类:${category}`;
    const response = await this.request({
      action: "query",
      list: "categorymembers",
      cmtitle: title,
      cmlimit: String(limit),
    });

    return response.query?.categorymembers || [];
  }

  // 获取图片信息。只解析 URL 和元数据，不下载图片文件。
  async get_image_info(filenames) {
    const names = Array.isArray(filenames) ? filenames : [filenames];
    const cleanNames = [...new Set(names.filter(Boolean))];
    const chunks = [];

    for (let index = 0; index < cleanNames.length; index += 50) {
      chunks.push(cleanNames.slice(index, index + 50));
    }

    const images = [];
    for (const chunk of chunks) {
      const titles = chunk
        .map((name) => (name.startsWith("File:") || name.startsWith("文件:") ? name : `File:${name}`))
        .join("|");

      const response = await this.request({
        action: "query",
        prop: "imageinfo",
        titles,
        iiprop: "url|mime|size|dimensions",
      });

      for (const page of response.query?.pages || []) {
        const info = page.imageinfo?.[0];
        images.push({
          title: page.title,
          name: page.title.replace(/^(File|文件):/, ""),
          file_page: `https://f7d.huijiwiki.com/wiki/${encodeURIComponent(page.title).replace(/%20/g, "_")}`,
          url: info?.url || "",
          mime: info?.mime || "",
          size: info?.size || null,
          width: info?.width || null,
          height: info?.height || null,
          missing: Boolean(page.missing),
        });
      }
    }

    return images;
  }

  // 页面列表接口。第一版仅提供 API 封装，不做全站同步。
  async list_all_pages(limit = 50, from = null) {
    const params = {
      action: "query",
      list: "allpages",
      aplimit: String(limit),
    };

    if (from) {
      params.apfrom = from;
    }

    const response = await this.request(params);
    return {
      pages: response.query?.allpages || [],
      continue: response.continue || null,
    };
  }

  #buildApiUrl(params) {
    const query = new URLSearchParams({
      format: "json",
      formatversion: "2",
      ...params,
    });

    return `${this.apiEndpoint}?${query.toString()}`;
  }
}

module.exports = {
  WikiClient,
};

const path = require("node:path");
const { BrowserManager } = require("../src/browser-manager");

// 七日之都灰机 Wiki 首页：先打开它，用真实浏览器会话通过 Cloudflare。
const HOME_URL = "https://f7d.huijiwiki.com/wiki/%E9%A6%96%E9%A1%B5";

// MediaWiki API 入口。
const API_ENDPOINT = "https://f7d.huijiwiki.com/api.php";

// 探针关注的关键词。后续正式采集器会根据这些结果扩展到角色、组织、剧情和世界观。
const KEYWORDS = ["神器使", "爱缪莎", "中央庭", "剧情", "赛斯", "幽桐", "拉比", "冈部伦太郎", "格蕾莎"];

function buildApiUrl(params) {
  const query = new URLSearchParams({
    format: "json",
    formatversion: "2",
    ...params,
  });

  return `${API_ENDPOINT}?${query.toString()}`;
}

async function fetchJson(browser, params) {
  const url = buildApiUrl(params);
  const result = await browser.download(url, null, {
    headers: {
      accept: "application/json,text/plain,*/*",
    },
    throwOnError: false,
  });

  const text = result.buffer.toString("utf8");

  if (result.status !== 200 || !text.trim().startsWith("{")) {
    return {
      ok: false,
      status: result.status,
      contentType: result.headers["content-type"] || "",
      preview: text.slice(0, 300),
    };
  }

  return {
    ok: true,
    status: result.status,
    json: JSON.parse(text),
  };
}

async function fetchListProbe(browser, label, params, pickItems) {
  const response = await fetchJson(browser, params);

  if (!response.ok) {
    console.log(`\n[失败] ${label}`);
    console.log(`HTTP ${response.status} ${response.contentType}`);
    console.log(response.preview);
    return null;
  }

  const items = pickItems(response.json) || [];
  console.log(`\n[成功] ${label}：返回 ${items.length} 条样本`);
  for (const item of items.slice(0, 30)) {
    console.log(`- ${item}`);
  }

  return {
    json: response.json,
    items,
  };
}

async function probeKeyword(browser, keyword) {
  // 第一层：精确标题查询。适合确认“爱缪莎”“中央庭”这类页面是否存在。
  const exact = await fetchJson(browser, {
    action: "query",
    prop: "info",
    titles: keyword,
  });

  const exactPages = exact.ok ? exact.json.query?.pages || [] : [];
  const exactMatches = exactPages
    .filter((page) => !page.missing)
    .map((page) => page.title);

  // 第二层：标题前缀查询。适合查“剧情/xxx”“角色/xxx”等结构化页面。
  const prefix = await fetchJson(browser, {
    action: "query",
    list: "allpages",
    apprefix: keyword,
    aplimit: "8",
  });

  const prefixMatches = prefix.ok
    ? (prefix.json.query?.allpages || []).map((page) => page.title)
    : [];

  // 第三层：全文搜索。部分 MediaWiki 站点可能禁用或返回空结构，因此只作为附加信息。
  const search = await fetchJson(browser, {
    action: "query",
    list: "search",
    srsearch: keyword,
    srlimit: "8",
  });

  const searchMatches = search.ok
    ? (search.json.query?.search || []).map((item) => item.title)
    : [];

  const merged = [...new Set([...exactMatches, ...prefixMatches, ...searchMatches])];

  return {
    keyword,
    exactMatches,
    prefixMatches,
    searchMatches,
    merged,
    searchAvailable: search.ok && Array.isArray(search.json.query?.search),
  };
}

async function main() {
  const browser = new BrowserManager({
    profileDir: path.resolve(__dirname, "..", ".playwright-profile", "f7d-chrome"),
    artifactDir: path.resolve(__dirname, "..", "artifacts"),
    headless: false,
  });

  try {
    await browser.start();
    await browser.goto(HOME_URL);
    await browser.wait_ready({ timeout: 60_000, settleMs: 1000 });

    console.log("七日之都灰机 Wiki 采集探针开始。");

    const siteInfo = await fetchJson(browser, {
      action: "query",
      meta: "siteinfo",
      siprop: "general|statistics",
    });

    if (siteInfo.ok) {
      const general = siteInfo.json.query.general;
      const statistics = siteInfo.json.query.statistics;
      console.log("\n[成功] API 基础信息");
      console.log(`站点：${general.sitename}`);
      console.log(`MediaWiki：${general.generator}`);
      console.log(`页面数：${statistics.pages}`);
      console.log(`词条数：${statistics.articles}`);
      console.log(`图片数：${statistics.images}`);
    } else {
      console.log("\n[失败] API 基础信息");
      console.log(siteInfo.preview);
      return;
    }

    await fetchListProbe(
      browser,
      "分类接口 list=allcategories",
      {
        action: "query",
        list: "allcategories",
        aclimit: "50",
      },
      (json) => json.query.allcategories.map((category) => category.category)
    );

    await fetchListProbe(
      browser,
      "页面接口 list=allpages",
      {
        action: "query",
        list: "allpages",
        aplimit: "50",
      },
      (json) => json.query.allpages.map((page) => page.title)
    );

    await fetchListProbe(
      browser,
      "图片接口 list=allimages",
      {
        action: "query",
        list: "allimages",
        ailimit: "20",
        aiprop: "url|mime|size",
      },
      (json) =>
        json.query.allimages.map((image) => {
          const size = image.size ? `${image.size} bytes` : "unknown size";
          return `${image.name} | ${image.mime || "unknown"} | ${size} | ${image.url || "no url"}`;
        })
    );

    console.log("\n[关键词页面验证]");
    for (const keyword of KEYWORDS) {
      const result = await probeKeyword(browser, keyword);
      const titles = result.merged.slice(0, 8);
      console.log(`- ${keyword}：${titles.length ? titles.join(" / ") : "未找到样本"}`);
    }

    await fetchListProbe(
      browser,
      "剧情分类前缀 allcategories&acprefix=剧情",
      {
        action: "query",
        list: "allcategories",
        acprefix: "剧情",
        aclimit: "30",
      },
      (json) => json.query.allcategories.map((category) => category.category)
    );

    const screenshotPath = await browser.screenshot(
      path.resolve(__dirname, "..", "artifacts", "f7d-probe-finished.png")
    );
    console.log(`\n探针完成，截图已保存：${screenshotPath}`);
  } finally {
    await browser.close();
  }
}

main().catch((error) => {
  console.error("探针失败：", error);
  process.exitCode = 1;
});

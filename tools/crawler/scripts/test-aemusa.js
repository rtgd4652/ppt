const fs = require("node:fs");
const path = require("node:path");
const { BrowserManager } = require("../src/browser-manager");

// 单页测试目标：爱缪莎。
// 注意：本脚本只测试一个页面，不遍历全站、不下载全部页面。
const PAGE_TITLE = "爱缪莎";
const HOME_URL = "https://f7d.huijiwiki.com/wiki/%E9%A6%96%E9%A1%B5";
const API_ENDPOINT = "https://f7d.huijiwiki.com/api.php";

// 单页测试结果输出目录。后续正式知识库可以再迁移到 knowledge/characters。
const OUTPUT_DIR = path.resolve(__dirname, "..", "artifacts", "aemusa-test");

function buildApiUrl(params) {
  const query = new URLSearchParams({
    format: "json",
    formatversion: "2",
    ...params,
  });

  return `${API_ENDPOINT}?${query.toString()}`;
}

async function fetchJson(browser, params) {
  const result = await browser.download(buildApiUrl(params), null, {
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
      preview: text.slice(0, 500),
    };
  }

  return {
    ok: true,
    status: result.status,
    json: JSON.parse(text),
  };
}

function writeJson(filename, data) {
  fs.mkdirSync(OUTPUT_DIR, { recursive: true });
  const filePath = path.join(OUTPUT_DIR, filename);
  fs.writeFileSync(filePath, JSON.stringify(data, null, 2), "utf8");
  return filePath;
}

function writeText(filename, data) {
  fs.mkdirSync(OUTPUT_DIR, { recursive: true });
  const filePath = path.join(OUTPUT_DIR, filename);
  fs.writeFileSync(filePath, data, "utf8");
  return filePath;
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

    console.log(`开始单页测试：${PAGE_TITLE}`);

    // 1. 精确页面信息：确认页面是否存在。
    const pageInfo = await fetchJson(browser, {
      action: "query",
      prop: "info|categories",
      titles: PAGE_TITLE,
      cllimit: "50",
    });

    if (!pageInfo.ok) {
      console.log("[失败] 页面信息接口未返回 JSON");
      console.log(`HTTP ${pageInfo.status} ${pageInfo.contentType}`);
      console.log(pageInfo.preview);
      return;
    }

    const page = pageInfo.json.query.pages[0];
    if (!page || page.missing) {
      console.log(`[失败] 未找到页面：${PAGE_TITLE}`);
      writeJson("page-info.json", pageInfo.json);
      return;
    }

    console.log("[成功] 页面存在");
    console.log(`标题：${page.title}`);
    console.log(`pageid：${page.pageid}`);
    console.log(`最后修订：${page.touched || "未知"}`);

    const categories = (page.categories || []).map((item) => item.title.replace(/^分类:/, ""));
    console.log(`分类数量：${categories.length}`);
    for (const category of categories.slice(0, 20)) {
      console.log(`- ${category}`);
    }

    // 2. 解析页面：拿 HTML、图片名、链接和分类。只解析这一页。
    const parsed = await fetchJson(browser, {
      action: "parse",
      page: PAGE_TITLE,
      prop: "text|images|categories|links|displaytitle",
      redirects: "1",
      disableeditsection: "1",
    });

    if (!parsed.ok) {
      console.log("[失败] parse 接口未返回 JSON");
      console.log(`HTTP ${parsed.status} ${parsed.contentType}`);
      console.log(parsed.preview);
      return;
    }

    const parseData = parsed.json.parse;
    const html = parseData.text;
    const imageNames = parseData.images || [];
    const links = parseData.links || [];

    console.log("\n[成功] 页面解析完成");
    console.log(`HTML 长度：${html.length}`);
    console.log(`引用图片数量：${imageNames.length}`);
    console.log(`页面链接数量：${links.length}`);

    // 3. 仅对当前页面引用图片做 URL 查询，不下载图片文件。
    let imageInfo = null;
    if (imageNames.length > 0) {
      const titles = imageNames.slice(0, 50).map((name) => `File:${name}`).join("|");
      imageInfo = await fetchJson(browser, {
        action: "query",
        prop: "imageinfo",
        titles,
        iiprop: "url|mime|size|dimensions",
      });

      if (imageInfo.ok) {
        const imagePages = imageInfo.json.query.pages || [];
        const imageRows = imagePages
          .filter((item) => item.imageinfo && item.imageinfo[0])
          .map((item) => {
            const info = item.imageinfo[0];
            return {
              title: item.title,
              url: info.url,
              mime: info.mime,
              size: info.size,
              width: info.width,
              height: info.height,
            };
          });

        console.log(`图片 URL 可解析数量：${imageRows.length}`);
        for (const image of imageRows.slice(0, 10)) {
          console.log(`- ${image.title} | ${image.width}x${image.height} | ${image.url}`);
        }
      } else {
        console.log("[警告] 图片信息接口未返回 JSON");
      }
    }

    // 4. 保存单页测试产物，便于后续设计正式知识库字段。
    const pageInfoPath = writeJson("page-info.json", pageInfo.json);
    const parsePath = writeJson("parse.json", parsed.json);
    const htmlPath = writeText("aemusa.html", html);

    let imageInfoPath = null;
    if (imageInfo?.ok) {
      imageInfoPath = writeJson("image-info.json", imageInfo.json);
    }

    console.log("\n[完成] 爱缪莎单页测试产物");
    console.log(pageInfoPath);
    console.log(parsePath);
    console.log(htmlPath);
    if (imageInfoPath) {
      console.log(imageInfoPath);
    }
  } finally {
    await browser.close();
  }
}

main().catch((error) => {
  console.error("爱缪莎单页测试失败：", error);
  process.exitCode = 1;
});

const path = require("node:path");
const { BrowserManager } = require("../src/browser-manager");

// 七日之都灰机 Wiki 首页：用于触发 Cloudflare 浏览器验证与保存 Cookie。
const HOME_URL = "https://f7d.huijiwiki.com/wiki/%E9%A6%96%E9%A1%B5";

// MediaWiki API 探针：验证通过后应返回 JSON；如果仍被拦截，通常会返回 HTML challenge。
const API_URL =
  "https://f7d.huijiwiki.com/api.php?action=query&meta=siteinfo&siprop=general%7Cnamespaces%7Cstatistics&format=json";

async function main() {
  const browser = new BrowserManager({
    // 单独给七日之都 Wiki 使用一个 profile，避免之后和其他站点 Cookie 混在一起。
    profileDir: path.resolve(__dirname, "..", ".playwright-profile", "f7d-chrome"),
    artifactDir: path.resolve(__dirname, "..", "artifacts"),
    headless: false,
  });

  try {
    await browser.start();

    console.log("打开灰机 Wiki 首页，用于建立浏览器会话：");
    console.log(HOME_URL);
    await browser.goto(HOME_URL);

    console.log("等待页面稳定。如果出现 Cloudflare 验证，请在浏览器里手动完成。");
    await browser.wait_ready();

    const screenshotPath = await browser.screenshot(
      path.resolve(__dirname, "..", "artifacts", "f7d-homepage-check.png")
    );
    console.log(`已保存页面截图：${screenshotPath}`);

    console.log("使用同一浏览器会话测试 MediaWiki API：");
    console.log(API_URL);

    const apiResult = await browser.download(API_URL, null, {
      headers: {
        accept: "application/json,text/plain,*/*",
      },
      throwOnError: false,
    });

    const contentType = apiResult.headers["content-type"] || "";
    const body = apiResult.buffer.toString("utf8");

    if (contentType.includes("application/json") || body.trim().startsWith("{")) {
      const json = JSON.parse(body);
      console.log("API 可用：已收到 JSON。");
      console.log(JSON.stringify(json.query?.general || json, null, 2));
    } else {
      console.log("API 尚未返回 JSON，可能仍被 Cloudflare 或站点策略拦截。");
      console.log(`HTTP 状态：${apiResult.status}`);
      console.log(`Content-Type：${contentType}`);
      console.log(body.slice(0, 500));
    }

    console.log("检查结束。浏览器会话已保存，下次运行会复用。");
  } finally {
    await browser.close();
  }
}

main().catch((error) => {
  console.error("检查失败：", error);
  process.exitCode = 1;
});

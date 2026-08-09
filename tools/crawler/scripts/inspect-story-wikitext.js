const path = require("node:path");
const { BrowserManager } = require("../src/browser-manager");
const { WikiClient } = require("../src/wiki-client");

const HOME_URL = "https://f7d.huijiwiki.com/wiki/%E9%A6%96%E9%A1%B5";
const title = process.argv.slice(2).join(" ").trim();

if (!title) {
  throw new Error("请提供一个明确的 Wiki 页面标题。");
}

async function main() {
  const browser = new BrowserManager({
    // 复用已经通过验证的项目专用会话，不读取个人浏览器资料。
    profileDir: path.resolve(__dirname, "..", ".playwright-profile", "f7d-chrome"),
    artifactDir: path.resolve(__dirname, "..", "artifacts"),
    headless: false,
  });

  try {
    await browser.start();
    await browser.goto(HOME_URL);
    await browser.wait_ready({ timeout: 60_000, settleMs: 1000 });

    const page = await new WikiClient(browser).get_wikitext(title);
    process.stdout.write(page.wikitext);
  } finally {
    await browser.close();
  }
}

main().catch((error) => {
  console.error("Wiki 文本检查失败：", error);
  process.exitCode = 1;
});

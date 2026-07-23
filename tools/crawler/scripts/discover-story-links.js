const fs = require("node:fs");
const path = require("node:path");
const { BrowserManager } = require("../src/browser-manager");
const { WikiClient } = require("../src/wiki-client");

const HOME_URL = "https://f7d.huijiwiki.com/wiki/%E9%A6%96%E9%A1%B5";
const rootTitle = process.argv.slice(2).join(" ").trim() || "正轨的箱庭/剧情/第七天";

function safeFilename(title) {
  return String(title || "untitled").replace(/[<>:"/\\|?*\u0000-\u001F]/g, "_").trim();
}

function linkTitle(link) {
  return String(link?.["*"] || link?.title || "").trim();
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

    const page = await new WikiClient(browser).get_page(rootTitle);
    // 只输出与当前剧情命名空间相近的候选链接，绝不据此自动抓取全站。
    const candidates = [...new Set(
      (page.links || [])
        .filter((link) => link && (link.ns === 0 || link.ns === "0" || link.ns === undefined))
        .map(linkTitle)
        .filter((title) => title.includes("/剧情/") || title.includes("正轨的箱庭"))
    )].sort((left, right) => left.localeCompare(right, "zh-Hans-CN"));

    const outputDir = path.resolve(__dirname, "..", "..", "..", "indexes", "story_pages", "discovery");
    fs.mkdirSync(outputDir, { recursive: true });
    const outputPath = path.join(outputDir, `${safeFilename(page.title)}.links.json`);
    const payload = {
      root_title: page.title,
      root_source_url: page.sourceUrl,
      discovered_at: new Date().toISOString(),
      candidate_pages: candidates,
      notes: [
        "这是从单一剧情页发现的候选链接，不等同于全站同步清单。",
        "写入正式批量清单前，应按主线、角色支线、活动剧情和项目排除规则人工分类。",
      ],
    };
    fs.writeFileSync(outputPath, JSON.stringify(payload, null, 2), "utf8");

    console.log(`剧情候选链接已写入：${outputPath}`);
    console.log(`候选页面数量：${candidates.length}`);
    for (const candidate of candidates) {
      console.log(`- ${candidate}`);
    }
  } finally {
    await browser.close();
  }
}

main().catch((error) => {
  console.error("剧情链接发现失败：", error);
  process.exitCode = 1;
});

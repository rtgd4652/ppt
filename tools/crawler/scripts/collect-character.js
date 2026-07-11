const path = require("node:path");
const { BrowserManager } = require("../src/browser-manager");
const { WikiClient } = require("../src/wiki-client");
const { Parser } = require("../src/parser");
const { CleanCharacterParser } = require("../src/clean-character-parser");
const { CharacterCollector } = require("../src/character-collector");

const HOME_URL = "https://f7d.huijiwiki.com/wiki/%E9%A6%96%E9%A1%B5";

// Milestone 1 验收对象：默认收集安托涅瓦。
// 这里不是特例逻辑；传入任意页面标题都走同一条 collect_character(title) 流程。
const title = process.argv.slice(2).join(" ").trim() || "安托涅瓦";

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

    const wikiClient = new WikiClient(browser);
    const rawParser = new Parser();
    const cleanParser = new CleanCharacterParser();
    const collector = new CharacterCollector({
      wikiClient,
      rawParser,
      cleanParser,
      outputRoot: path.resolve(__dirname, "..", "..", "..", "knowledge"),
      rawRoot: path.resolve(__dirname, "..", "..", "..", "raw"),
      indexRoot: path.resolve(__dirname, "..", "..", "..", "indexes"),
    });

    const result = await collector.collect_character(title);

    console.log("角色知识卡生成完成。");
    console.log(`标题：${result.title}`);
    console.log(`分类数量：${result.categoryCount}`);
    console.log(`链接数量：${result.linkCount}`);
    console.log(`图片索引数量：${result.imageCount}`);
    console.log(`Raw Markdown：${result.rawMarkdownPath}`);
    console.log(`Clean Markdown：${result.markdownPath}`);
    console.log(`图片索引：${result.imageIndexPath}`);
  } finally {
    await browser.close();
  }
}

main().catch((error) => {
  console.error("角色知识卡生成失败：", error);
  process.exitCode = 1;
});

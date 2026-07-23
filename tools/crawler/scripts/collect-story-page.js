const fs = require("node:fs");
const path = require("node:path");
const { BrowserManager } = require("../src/browser-manager");
const { WikiClient } = require("../src/wiki-client");
const { StoryParser } = require("../src/story-parser");
const { StoryCollector } = require("../src/story-collector");

const HOME_URL = "https://f7d.huijiwiki.com/wiki/%E9%A6%96%E9%A1%B5";
const MANUAL_CORRECTIONS_PATH = path.resolve(
  __dirname,
  "..",
  "..",
  "knowledge",
  "data",
  "story_manual_corrections_v0.1.json"
);

// 人工确认与自动采集分层保存：不存在校正文件时仍可照常采集普通页面。
function loadManualPageAnnotation(pageTitle) {
  if (!fs.existsSync(MANUAL_CORRECTIONS_PATH)) {
    return {};
  }

  const corrections = JSON.parse(fs.readFileSync(MANUAL_CORRECTIONS_PATH, "utf8"));
  return corrections.page_annotations?.[pageTitle] || {};
}
// 默认仍处理单页；传入 --batch 时在同一浏览器会话中按顺序处理多个明确页面。
// 批量模式只复用会话，不发现或扩展页面范围，因此仍符合“禁止全站同步”的采集原则。
const commandArgs = process.argv.slice(2);
const batchMode = commandArgs[0] === "--batch";
const titles = batchMode
  ? commandArgs.slice(1).map((value) => value.trim()).filter(Boolean)
  : [commandArgs.join(" ").trim() || "正轨的箱庭/剧情/第七天"];

if (titles.length === 0) {
  throw new Error("批量采集模式至少需要提供一个明确的 Wiki 页面标题。");
}

// 部分第一天和最终日页面以结局名作为 Wiki 路径前缀，但叙事上仍属于其母主线。
// 在采集阶段统一回填母路线，避免 raw、clean 和 SQLite 把结局名误登记成新的剧情路线。
const PAGE_CONTEXTS = new Map([
  ["牺牲的意义/剧情/最终日", { route: "正轨的箱庭", chapter: "主线剧情 1", day: "最终日（牺牲的意义）" }],
  ["箱庭风景/剧情/最终日", { route: "正轨的箱庭", chapter: "主线剧情 1", day: "最终日（箱庭风景）" }],
  ["终结/剧情/最终日", { route: "正轨的箱庭", chapter: "主线剧情 1", day: "最终日（终结）" }],
  ["两个人的旅途/剧情/第一天", { route: "无垢的人偶", chapter: "主线剧情 2", day: "第一天（两个人的旅途）" }],
  ["永恒的终焉/剧情/第一天", { route: "无垢的人偶", chapter: "主线剧情 2", day: "第一天（永恒的终焉）" }],
  ["两个人的旅途/剧情/最终日", { route: "无垢的人偶", chapter: "主线剧情 2", day: "最终日（两个人的旅途）" }],
  ["永恒的终焉/剧情/最终日", { route: "无垢的人偶", chapter: "主线剧情 2", day: "最终日（永恒的终焉）" }],
  ["深蓝之星/剧情/最终日", { route: "避世的方舟", chapter: "主线剧情 3", day: "最终日（深蓝之星）" }],
  ["黑暗中的身影/剧情/最终日", { route: "避世的方舟", chapter: "主线剧情 3", day: "最终日（黑暗中的身影）" }],
  ["终结（避世的方舟）/剧情/最终日", { route: "避世的方舟", chapter: "主线剧情 3", day: "最终日（终结）" }],
  // “深渊的步伐”从第三天起存在独立的“被抛下的人”页面分支。
  // 这些页面虽然不再使用母路线作为路径前缀，仍必须统一归档到主线剧情 4。
  ["被抛下的人/剧情/第三天", { route: "深渊的步伐", chapter: "主线剧情 4", day: "第三天（被抛下的人）" }],
  ["被抛下的人/剧情/第二天", { route: "深渊的步伐", chapter: "主线剧情 4", day: "第二天（被抛下的人）" }],
  ["被抛下的人/剧情/第一天", { route: "深渊的步伐", chapter: "主线剧情 4", day: "第一天（被抛下的人）" }],
  ["被抛下的人/剧情/最终日", { route: "深渊的步伐", chapter: "主线剧情 4", day: "最终日（被抛下的人）" }],
  ["神的棋盘/剧情/最终日", { route: "深渊的步伐", chapter: "主线剧情 4", day: "最终日（神的棋盘）" }],
  ["零的故事/剧情/最终日", { route: "深渊的步伐", chapter: "主线剧情 4", day: "最终日（零的故事）" }],
  // 三个特殊灭世页面属于本路线的失败状态，不应误登记为独立主线或普通结局。
  ["深渊的步伐/剧情/特殊灭世1", { route: "深渊的步伐", chapter: "主线剧情 4", day: "特殊灭世 1（研究所被中央庭攻占）" }],
  ["深渊的步伐/剧情/特殊灭世2", { route: "深渊的步伐", chapter: "主线剧情 4", day: "特殊灭世 2（剧情战失败）" }],
  ["深渊的步伐/剧情/特殊灭世3", { route: "深渊的步伐", chapter: "主线剧情 4", day: "特殊灭世 3（被抛下的人要求未达成）" }],
]);

// 已确认章节归属的主线名称集中维护：采集器只写入已有人工作为依据的分类，
// 其余路线继续保留“待人工分类”，避免根据标题自动臆测章节顺序。
const ROUTE_CONTEXTS = new Map([
  ["正轨的箱庭", { chapter: "主线剧情 1" }],
  ["无垢的人偶", { chapter: "主线剧情 2" }],
  ["避世的方舟", { chapter: "主线剧情 3" }],
  ["深渊的步伐", { chapter: "主线剧情 4" }],
]);

// 从标准“路线/剧情/阶段”页面名提取元数据，避免把第七天的标签错误复用到后续页面。
function inferStoryOptions(pageTitle) {
  const pageContext = PAGE_CONTEXTS.get(pageTitle);
  const marker = "/剧情/";
  const markerIndex = pageTitle.indexOf(marker);
  const route = markerIndex >= 0 ? pageTitle.slice(0, markerIndex) : "";
  const stage = markerIndex >= 0 ? pageTitle.slice(markerIndex + marker.length) : "";
  const routeContext = ROUTE_CONTEXTS.get(route);
  const annotation = loadManualPageAnnotation(pageTitle);

  return {
    storyScope: pageContext || route ? "main_story" : "unclassified",
    route: pageContext?.route || route,
    // 结局别名页优先使用页面级归属；普通页面再使用已确认的主线路线表。
    chapter: pageContext?.chapter || routeContext?.chapter || "待人工分类",
    day: pageContext?.day || stage || "待确认",
    legacyVideoEvidence: ["Bilibili BV17M4y1w7rr：仅保留为既有补充记录，不作为正文主来源"],
    manualStructureNote: annotation.manual_structure_note || "",
    manualStructureReference: annotation.manual_structure_reference || "",
  };
}

async function main() {
  const browser = new BrowserManager({
    // 继续复用已经通过灰机 Wiki 验证的专用会话，不读取个人浏览器资料。
    profileDir: path.resolve(__dirname, "..", ".playwright-profile", "f7d-chrome"),
    artifactDir: path.resolve(__dirname, "..", "artifacts"),
    headless: false,
  });

  try {
    await browser.start();
    await browser.goto(HOME_URL);
    await browser.wait_ready({ timeout: 60_000, settleMs: 1000 });

    const collector = new StoryCollector({
      wikiClient: new WikiClient(browser),
      storyParser: new StoryParser(),
      outputRoot: path.resolve(__dirname, "..", "..", "..", "knowledge"),
      rawRoot: path.resolve(__dirname, "..", "..", "..", "raw"),
      indexRoot: path.resolve(__dirname, "..", "..", "..", "indexes"),
    });

    for (const title of titles) {
      const result = await collector.collect_story_page(title, inferStoryOptions(title));

      console.log("剧情 Wiki 页面采集完成。");
      console.log(`标题：${result.title}`);
      console.log(`章节数量：${result.sectionCount}`);
      console.log(`页面链接数量：${result.linkCount}`);
      console.log(`Raw Markdown：${result.rawMarkdownPath}`);
      console.log(`Clean Markdown：${result.markdownPath}`);
      console.log(`来源索引：${result.sourceIndexPath}`);
    }
  } finally {
    await browser.close();
  }
}

main().catch((error) => {
  console.error("剧情 Wiki 页面采集失败：", error);
  process.exitCode = 1;
});

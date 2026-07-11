const fs = require("node:fs");
const path = require("node:path");
const { BrowserManager } = require("../src/browser-manager");
const { WikiClient } = require("../src/wiki-client");
const { Parser } = require("../src/parser");
const { CleanCharacterParser } = require("../src/clean-character-parser");
const { CharacterCollector } = require("../src/character-collector");

const HOME_URL = "https://f7d.huijiwiki.com/wiki/%E9%A6%96%E9%A1%B5";

// Milestone 1.2 指定回归名单。注意：这里只跑指定名单，不做全站同步。
const TARGET_CHARACTERS = ["安托涅瓦", "爱缪莎", "晏华", "赛斯", "幽桐", "拉比", "格蕾莎"];

const REQUIRED_SECTIONS = [
  "简介",
  "基本资料",
  "神器",
  "神器故事",
  "能力",
  "日常故事",
  "羁绊片段",
  "回忆片段",
  "同伴评价",
  "MOD 可用设定摘录",
];

const OUTPUT_ROOT = path.resolve(__dirname, "..", "..", "..", "knowledge");
const RAW_ROOT = path.resolve(__dirname, "..", "..", "..", "raw");
const INDEX_ROOT = path.resolve(__dirname, "..", "..", "..", "indexes");
const REPORT_DIR = path.resolve(__dirname, "..", "..", "..", "reports");
const REPORT_PATH = path.join(REPORT_DIR, "character_collect_report.md");

function safeFilename(title) {
  return title.replace(/[<>:"/\\|?*\u0000-\u001F]/g, "_").trim();
}

function countImages(imageIndexPath) {
  if (!fs.existsSync(imageIndexPath)) {
    return 0;
  }

  const data = JSON.parse(fs.readFileSync(imageIndexPath, "utf8"));
  return Object.values(data.images || {}).reduce((sum, bucket) => sum + (Array.isArray(bucket) ? bucket.length : 0), 0);
}

function validateCharacter(title) {
  const filename = safeFilename(title);
  const rawPath = path.join(RAW_ROOT, "huiji", "characters", `${filename}.raw.md`);
  const markdownPath = path.join(OUTPUT_ROOT, "characters", `${filename}.md`);
  const imageIndexPath = path.join(INDEX_ROOT, "images", `${filename}.images.json`);

  const warnings = [];
  const missingSections = [];

  if (!fs.existsSync(rawPath)) {
    warnings.push("缺少 raw Markdown。");
  }
  if (!fs.existsSync(markdownPath)) {
    warnings.push("缺少 clean Markdown。");
  }
  if (!fs.existsSync(imageIndexPath)) {
    warnings.push("缺少图片索引。");
  }

  if (fs.existsSync(markdownPath)) {
    const markdown = fs.readFileSync(markdownPath, "utf8");
    if (!markdown.startsWith("---\n")) {
      warnings.push("Front Matter 起始缺失。");
    }
    if (!/\n---\n\n# 简介/.test(markdown)) {
      warnings.push("Front Matter 结束或正文起点异常。");
    }
    if (/^images:/m.test(markdown)) {
      warnings.push("Front Matter 中仍包含 images 字段。");
    }

    for (const section of REQUIRED_SECTIONS) {
      if (!markdown.includes(`# ${section}`)) {
        missingSections.push(section);
      }
    }

    const ability = markdown.split("# 能力")[1]?.split("# 日常故事")[0] || "";
    if (/神器技能/.test(ability)) {
      warnings.push("能力章节疑似混入神器技能。");
    }

    const bond = markdown.split("# 羁绊片段")[1]?.split("# 回忆片段")[0] || "";
    if (/回忆片段\d*/.test(bond)) {
      warnings.push("羁绊片段中疑似混入回忆片段。");
    }

    const memory = markdown.split("# 回忆片段")[1]?.split("# 同伴评价")[0] || "";
    if (/回顾\s*$/m.test(memory)) {
      warnings.push("回忆片段仍存在行尾“回顾”。");
    }

    const daily = markdown.split("# 日常故事")[1]?.split("# 羁绊片段")[0] || "";
    if (/同伴评价|^- .+：/m.test(daily)) {
      warnings.push("日常故事中疑似混入同伴评价。");
    }

    const isolatedResidual = markdown.match(/^(能力|回忆|技能|情报|描述|等级)$/gm);
    if (isolatedResidual?.length) {
      warnings.push(`存在孤立残留词：${[...new Set(isolatedResidual)].join("、")}`);
    }
  }

  if (missingSections.length) {
    warnings.push(`缺失章节：${missingSections.join("、")}`);
  }

  return {
    title,
    success: fs.existsSync(rawPath) && fs.existsSync(markdownPath) && fs.existsSync(imageIndexPath) && missingSections.length === 0,
    missingSections,
    imageCount: countImages(imageIndexPath),
    warnings,
    paths: {
      rawPath,
      markdownPath,
      imageIndexPath,
    },
  };
}

function buildReport(results) {
  const lines = [];
  lines.push("# 角色采集回归测试报告");
  lines.push("");
  lines.push(`生成时间：${new Date().toISOString()}`);
  lines.push("");
  lines.push("本报告只覆盖 Milestone 1.2 指定角色名单，不代表全站同步。");
  lines.push("");
  lines.push("| 角色名 | 是否成功 | 缺失章节 | 图片数量 | 警告信息 |");
  lines.push("|---|---:|---|---:|---|");

  for (const result of results) {
    lines.push(
      `| ${result.title} | ${result.success ? "是" : "否"} | ${
        result.missingSections.length ? result.missingSections.join("、") : "无"
      } | ${result.imageCount} | ${result.warnings.length ? result.warnings.join("<br>") : "无"} |`
    );
  }

  lines.push("");
  lines.push("## 输出文件路径");
  lines.push("");
  for (const result of results) {
    lines.push(`### ${result.title}`);
    lines.push("");
    lines.push(`- raw：${result.paths.rawPath}`);
    lines.push(`- clean：${result.paths.markdownPath}`);
    lines.push(`- images：${result.paths.imageIndexPath}`);
    lines.push("");
  }

  return `${lines.join("\n")}\n`;
}

async function main() {
  const browser = new BrowserManager({
    profileDir: path.resolve(__dirname, "..", ".playwright-profile", "f7d-chrome"),
    artifactDir: path.resolve(__dirname, "..", "artifacts"),
    headless: false,
  });

  const results = [];

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
      outputRoot: OUTPUT_ROOT,
      rawRoot: RAW_ROOT,
      indexRoot: INDEX_ROOT,
    });

    for (const title of TARGET_CHARACTERS) {
      console.log(`采集角色：${title}`);
      try {
        await collector.collect_character(title);
        results.push(validateCharacter(title));
      } catch (error) {
        const failed = validateCharacter(title);
        failed.success = false;
        failed.warnings.push(`采集失败：${error.message}`);
        results.push(failed);
      }
    }
  } finally {
    await browser.close();
  }

  fs.mkdirSync(REPORT_DIR, { recursive: true });
  fs.writeFileSync(REPORT_PATH, buildReport(results), "utf8");

  console.log("角色采集回归测试完成。");
  console.log(`报告：${REPORT_PATH}`);

  const failedCount = results.filter((result) => !result.success).length;
  if (failedCount > 0) {
    process.exitCode = 1;
  }
}

main().catch((error) => {
  console.error("角色采集回归测试失败：", error);
  process.exitCode = 1;
});

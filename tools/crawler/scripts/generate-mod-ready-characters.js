const fs = require("node:fs");
const path = require("node:path");
const { ModReadyGenerator, REQUIRED_SECTIONS } = require("../src/mod-ready-generator");

const TARGET_CHARACTERS = ["安托涅瓦", "爱缪莎", "晏华", "赛斯", "幽桐", "拉比", "格蕾莎"];

const REPO_ROOT = path.resolve(__dirname, "..", "..", "..");
const INPUT_DIR = path.join(REPO_ROOT, "knowledge", "characters");
const OUTPUT_DIR = path.join(REPO_ROOT, "knowledge", "mod_ready", "characters");
const REPORT_DIR = path.join(REPO_ROOT, "reports");
const REPORT_PATH = path.join(REPORT_DIR, "mod_ready_character_report.md");

function safeFilename(title) {
  return title.replace(/[<>:"/\\|?*\u0000-\u001F]/g, "_").trim();
}

function validateModMarkdown(markdown) {
  const missingSections = REQUIRED_SECTIONS.filter((section) => !markdown.includes(`# ${section}`));
  const warnings = [];

  if (!markdown.startsWith("---\n")) {
    warnings.push("Front Matter 起始缺失。");
  }
  if (!/\n---\n\n# 角色定位/.test(markdown)) {
    warnings.push("Front Matter 结束或正文起点异常。");
  }

  return {
    missingSections,
    warnings,
  };
}

function buildReport(results) {
  const lines = [];
  lines.push("# MOD 摘要角色生成报告");
  lines.push("");
  lines.push(`生成时间：${new Date().toISOString()}`);
  lines.push("");
  lines.push("本报告只覆盖 Milestone 1.3 指定角色名单；输入为 clean markdown，未修改原始采集器。");
  lines.push("");
  lines.push("| 角色名 | 是否成功 | 缺失章节 | 警告信息 | 输入文件 | 输出文件 |");
  lines.push("|---|---:|---|---|---|---|");

  for (const result of results) {
    lines.push(
      `| ${result.title} | ${result.success ? "是" : "否"} | ${
        result.missingSections.length ? result.missingSections.join("、") : "无"
      } | ${result.warnings.length ? result.warnings.join("<br>") : "无"} | ${result.inputPath} | ${result.outputPath} |`
    );
  }

  return `${lines.join("\n")}\n`;
}

function main() {
  const generator = new ModReadyGenerator();
  const results = [];

  fs.mkdirSync(OUTPUT_DIR, { recursive: true });

  for (const title of TARGET_CHARACTERS) {
    const filename = safeFilename(title);
    const inputPath = path.join(INPUT_DIR, `${filename}.md`);
    const outputPath = path.join(OUTPUT_DIR, `${filename}.mod.md`);
    const result = {
      title,
      success: false,
      missingSections: [],
      warnings: [],
      inputPath,
      outputPath,
    };

    try {
      if (!fs.existsSync(inputPath)) {
        throw new Error("输入 clean markdown 不存在。");
      }

      const cleanMarkdown = fs.readFileSync(inputPath, "utf8");
      const modMarkdown = generator.generateFromCleanMarkdown(cleanMarkdown);
      fs.writeFileSync(outputPath, modMarkdown, "utf8");

      const validation = validateModMarkdown(modMarkdown);
      result.missingSections = validation.missingSections;
      result.warnings = validation.warnings;
      result.success = result.missingSections.length === 0 && result.warnings.length === 0;
    } catch (error) {
      result.warnings.push(error.message);
    }

    results.push(result);
  }

  fs.mkdirSync(REPORT_DIR, { recursive: true });
  fs.writeFileSync(REPORT_PATH, buildReport(results), "utf8");

  console.log("MOD 摘要角色生成完成。");
  console.log(`报告：${REPORT_PATH}`);

  if (results.some((result) => !result.success)) {
    process.exitCode = 1;
  }
}

main();

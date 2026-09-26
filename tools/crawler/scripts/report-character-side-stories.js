const fs = require("node:fs");
const path = require("node:path");

const REPOSITORY_ROOT = path.resolve(__dirname, "..", "..", "..");
const MANIFEST_PATH = path.join(
  REPOSITORY_ROOT,
  "tools",
  "knowledge",
  "data",
  "character_side_story_manifest_v1.0.json"
);
const REPORT_PATH = path.join(REPOSITORY_ROOT, "reports", "character_side_story_collect_report.md");
const CURATED_MANIFEST_PATH = path.join(
  REPOSITORY_ROOT,
  "tools",
  "knowledge",
  "data",
  "story_curated_manifest_v0.1.json"
);

function readJson(filePath) {
  return JSON.parse(fs.readFileSync(filePath, "utf8"));
}

function relativePath(filePath) {
  return path.relative(REPOSITORY_ROOT, filePath).split(path.sep).join("/");
}

function safeFilename(title) {
  return String(title).replace(/[<>:"/\\|?*\u0000-\u001F]/g, "_").trim();
}

function inspectEntry(entry, curatedBySourceTitle) {
  const stem = safeFilename(entry.page_title);
  const rawPath = path.join(REPOSITORY_ROOT, "raw", "huiji", "stories", `${stem}.raw.md`);
  const cleanPath = path.join(REPOSITORY_ROOT, "knowledge", "story", "pages", `${stem}.md`);
  const sourcePath = path.join(REPOSITORY_ROOT, "indexes", "story_pages", `${stem}.source.json`);
  const missing = [rawPath, cleanPath, sourcePath].filter((filePath) => !fs.existsSync(filePath));

  if (missing.length) {
    return {
      ...entry,
      success: false,
      missing,
      rawPath,
      cleanPath,
      sourcePath,
      warnings: ["三件套输出不完整。"],
    };
  }

  const source = readJson(sourcePath);
  const clean = fs.readFileSync(cleanPath, "utf8");
  const curated = curatedBySourceTitle.get(entry.page_title) || null;
  const warnings = [];
  if (source.story_scope !== "character_side_story") {
    warnings.push(`剧情范围异常：${source.story_scope || "空"}`);
  }
  if (!Array.isArray(source.choice_trees)) {
    warnings.push("来源索引缺少 choice_trees 数组。" );
  }
  if (/(?:Mission[ _-]?type[ _-]?Role|CG[ _-]?(?:clear|\d+)|Item[ _-]?event[ _-]?\d+|Bg[ _-]?event[ _-]?show)\.(?:png|jpe?g|gif|webp|svg)/i.test(clean)) {
    warnings.push("clean 文本仍含已知视觉资源文件名残留。" );
  }
  if (clean.length < 1000) {
    warnings.push("clean 正文长度异常偏短，需人工检查来源页。" );
  }

  return {
    ...entry,
    success: warnings.length === 0,
    rawPath,
    cleanPath,
    sourcePath,
    sectionCount: Array.isArray(source.sections) ? source.sections.length : 0,
    choiceTreeCount: Array.isArray(source.choice_trees) ? source.choice_trees.length : 0,
    characterCount: clean.length,
    lastSync: source.last_sync || "",
    curated,
    warnings,
  };
}

function main() {
  const manifest = readJson(MANIFEST_PATH);
  // 人工整理状态来自统一清单，避免报告重新生成后退回“待校订”。
  const curatedManifest = readJson(CURATED_MANIFEST_PATH);
  const curatedBySourceTitle = new Map(
    curatedManifest.documents.map((document) => [document.source_page_title, document])
  );
  const results = manifest.collected_characters.map((entry) =>
    inspectEntry(entry, curatedBySourceTitle)
  );
  const passed = results.filter((result) => result.success).length;
  const approved = results.filter(
    (result) => result.curated?.document_status === "human_review_approved"
  ).length;
  const lines = [
    "# 神器使个人支线采集报告",
    "",
    `- 清单版本：${manifest.version}`,
    `- 来源入口：${manifest.source_root}`,
    `- 已通过：${passed}/${results.length}`,
    `- 人工校订：${approved}/${results.length}`,
    "- 当前阶段：八名原作神器使个人支线已完成采集、结构检查与整名角色人工校订。",
    "",
    "## 采集结果",
    "",
    "| 角色 | 状态 | 剧情段落 | 选择树 | Clean 字符数 | 警告 |",
    "|---|---:|---:|---:|---:|---|",
  ];

  for (const result of results) {
    lines.push(
      `| ${result.character} | ${result.success ? "通过" : "需检查"} | ${result.sectionCount || 0} | ${result.choiceTreeCount || 0} | ${result.characterCount || 0} | ${result.warnings.join("；") || "无"} |`
    );
  }

  lines.push("", "## 输出文件", "");
  for (const result of results) {
    lines.push(
      `### ${result.character}`,
      "",
      `- Raw：\`${relativePath(result.rawPath)}\``,
      `- Clean：\`${relativePath(result.cleanPath)}\``,
      `- 来源索引：\`${relativePath(result.sourcePath)}\``,
      `- 人工整理：${result.curated ? `\`${result.curated.file_path}\`` : "未登记"}`,
      `- 审核状态：${result.curated?.document_status || "未审核"}`,
      `- 最近同步：${result.lastSync || "未生成"}`,
      ""
    );
  }

  lines.push("## 已确认无个人支线的角色", "");
  for (const entry of manifest.known_exceptions) {
    lines.push(`- **${entry.character}**：${entry.reason}`);
  }

  lines.push("", "## 单独来源范围", "");
  for (const entry of manifest.separate_source_scope) {
    lines.push(`- **${entry.character}**：${entry.reason}`);
  }

  lines.push(
    "",
    "## 已执行的人工校订规则",
    "",
    "1. 按页面剧情段落逐段确认人物行为、关系、价值选择与结局。",
    "2. 对每棵选择树确认选项、对应回答、是否可重复以及共同后续内容。",
    "3. 攻略条件与系统提示保留为来源上下文，不直接写入项目角色正史。",
    "4. 有疑义的事实进入审核项，不从单一对白自动推导世界观结论。",
    ""
  );

  fs.mkdirSync(path.dirname(REPORT_PATH), { recursive: true });
  fs.writeFileSync(REPORT_PATH, lines.join("\n"), "utf8");

  console.log(`个人支线报告已生成：${REPORT_PATH}`);
  console.log(`通过：${passed}/${results.length}`);
  if (passed !== results.length) {
    process.exitCode = 1;
  }
}

main();

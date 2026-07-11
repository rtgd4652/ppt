const fs = require("node:fs");
const path = require("node:path");
const {
  REPOSITORY_ROOT,
  formatDuration,
  getCatalogRows,
  getCharacterSourceRows,
  loadMainStoryCatalog,
  openKnowledgeDatabase,
  syncExistingCharacterSources,
  syncMainStoryCatalog,
} = require("./knowledge-db");

const CURATED_ROOT = path.join(REPOSITORY_ROOT, "knowledge", "curated");
const SOURCE_OUTPUT = path.join(CURATED_ROOT, "sources", "bilibili_main_story_BV17M4y1w7rr.md");
const CATALOG_OUTPUT = path.join(CURATED_ROOT, "videos", "main_story_catalog_v0.1.md");
const REVIEW_OUTPUT = path.join(CURATED_ROOT, "reviews", "main_story_core_01_03_review_queue_v0.1.md");
const HUIJI_SOURCE_OUTPUT = path.join(CURATED_ROOT, "sources", "huiji_character_source_index_v0.1.md");
const REPORT_OUTPUT = path.join(REPOSITORY_ROOT, "reports", "knowledge_database_bootstrap_report.md");

function writeText(filePath, content) {
  fs.mkdirSync(path.dirname(filePath), { recursive: true });
  fs.writeFileSync(filePath, `${content.trim()}\n`, "utf8");
}

function sourceRecordMarkdown(source, result) {
  return `
# 剧情视频来源记录：${source.id}

## 基础信息

- 平台：${source.provider}
- 类型：${source.type}
- 标题：${source.title}
- 上传者：${source.uploader}
- 页面：${source.url}
- 发布日期：${source.published_on}
- 已索引分集：${result.episodeCount}
- 目录总时长：${formatDuration(result.totalDurationSeconds)}

## 项目中的证据地位

- 来源性质：社区上传的主线剧情录像，不是官方文字资料。
- 项目授权定位：${source.project_authority}。
- 使用范围：${source.scope}
- 覆盖说明：${source.coverage_note}
- 采集限制：不下载视频、不保存视频帧、不复制长篇台词；只记录分集目录、时间码和原创摘要。

## 使用规则

1. 视频可用于补足 Wiki 缺失的主线剧情过程与顺序。
2. 任何进入正式知识层的事实必须附分集编号、起止时间码和人工审核结果。
3. 与 Wiki 或现有设定矛盾的内容先标记为“需要特殊补充”，不得直接覆盖确认事实。
4. 第 12 章《堕天使的挽歌》按项目编辑决定排除，不作为剧情采集依据。
`;
}

function huijiSourceIndexMarkdown(rows) {
  const lines = [];
  lines.push("# 灰机 Wiki 角色来源索引 v0.1");
  lines.push("");
  lines.push("> 本索引由本地 SQLite 数据库导出。它登记采集来源，不表示页面中的每项内容均已人工确认。");
  lines.push("");
  lines.push("| 来源 ID | 角色 | 页面 |");
  lines.push("| --- | --- | --- |");
  for (const row of rows) {
    lines.push(`| ${row.source_id} | ${row.title} | ${row.canonical_url} |`);
  }
  return lines.join("\n");
}

function catalogMarkdown(source, rows, result) {
  const lines = [];
  lines.push("# 主线剧情视频目录 v0.1");
  lines.push("");
  lines.push(`> 来源：${source.title}（${source.id}）。`);
  lines.push("> 本目录是本地知识库的可审阅视图；结构化记录保存在本地 SQLite 数据库中。");
  lines.push("");
  lines.push("## 目录范围");
  lines.push("");
  lines.push(`- 已索引分集：${result.episodeCount}`);
  lines.push(`- 总时长：${formatDuration(result.totalDurationSeconds)}`);
  lines.push(`- 首批审核队列：${result.priorityCount} 集（第 1 至 3 章及其必要上下文）`);
  lines.push(`- 编辑排除：${result.excludedCount} 集（第 12 章）`);
  lines.push("- 当前阶段：只完成目录与审核队列，不代表已经观看、摘要或确认全部剧情。");
  lines.push("");
  lines.push("## 分集清单");
  lines.push("");
  lines.push("| 分集 | 范围 | 标题 | 时长 | 状态 |");
  lines.push("| ---: | --- | --- | --- | --- |");

  for (const row of rows) {
    const scope = row.chapter_number
      ? `主线 ${row.chapter_number}${row.chapter_label ? `：${row.chapter_label}` : ""}`
      : row.content_kind === "prologue"
        ? "引子"
        : row.content_kind === "bonus"
          ? "彩蛋"
          : "城市区段";
    const status = row.editorial_status === "excluded"
      ? "排除"
      : row.priority_batch
        ? "首批待审"
        : "待审";
    lines.push(`| P${String(row.episode_no).padStart(2, "0")} | ${scope} | ${row.title} | ${row.duration_display} | ${status} |`);
  }

  lines.push("");
  lines.push("## 排除说明");
  lines.push("");
  lines.push("- P34、P35 属于第 12 章《堕天使的挽歌》，按项目编辑决定不进行剧情采集、摘要或世界观引用。目录保留这两条记录仅用于防止未来误收录。");
  return lines.join("\n");
}

function reviewQueueMarkdown(source, rows) {
  const lines = [];
  lines.push("# 主线第 1 至 3 章人工摘要审核队列");
  lines.push("");
  lines.push(`> 视频来源：${source.id}。本队列覆盖 P01 至 P12，不自动转写，不复制完整对白。`);
  lines.push("");
  lines.push("## 使用方法");
  lines.push("");
  lines.push("1. 观看指定分集并记录最小必要时间码。\n2. 用自己的话填写剧情摘要。\n3. 将可进入知识库的事实写入候选事实栏。\n4. 人工标记“已确认 / 保留疑问 / 不采用”。\n5. 只有“已确认”事实才能迁入 curated 世界观或角色条目。");

  for (const row of rows.filter((item) => item.priority_batch === "core_chapters_01_03")) {
    lines.push("");
    lines.push(`## P${String(row.episode_no).padStart(2, "0")}：${row.title}`);
    lines.push("");
    lines.push(`- 时长：${row.duration_display}`);
    lines.push(`- 目录定位：${row.chapter_number ? `主线 ${row.chapter_number}` : "引子 / 上下文"}`);
    lines.push("- 观看状态：未开始");
    lines.push("- 时间码：待填写");
    lines.push("- 原创摘要：待填写");
    lines.push("- 候选事实：待填写");
    lines.push("- 与 Wiki 的关系：待比对");
    lines.push("- 审核结果：待审核");
    lines.push("- 特殊补充：无");
  }

  return lines.join("\n");
}

function reportMarkdown(result, characterResult) {
  return `
# 本地知识库数据库初始化报告

- 数据库：` + "`knowledge/database/seven_days_knowledge.sqlite`" + `（本地生成，不提交二进制文件）
- 结构化视频来源记录：1
- 灰机角色来源记录：${characterResult.characterSourceCount}
- 已索引 Clean 角色文档：${characterResult.cleanCharacterCount}
- 主线视频分集记录：${result.episodeCount}
- 目录总时长：${formatDuration(result.totalDurationSeconds)}
- 第 12 章排除记录：${result.excludedCount}
- 首批人工摘要队列：${result.priorityCount}

## 当前范围

- 已建立：来源记录、视频目录、审核状态字段、事实与证据表结构。
- 未开始：视频观看、剧情摘要、时间码事实录入、正式世界观文档重写。
- 未进行：视频下载、音频转写、图片下载、全站 Wiki 同步。
`;
}

const database = openKnowledgeDatabase();

try {
  const result = syncMainStoryCatalog(database);
  const characterResult = syncExistingCharacterSources(database);
  const catalog = loadMainStoryCatalog();
  const rows = getCatalogRows(database, catalog.source.id);
  const characterSources = getCharacterSourceRows(database);

  writeText(SOURCE_OUTPUT, sourceRecordMarkdown(catalog.source, result));
  writeText(CATALOG_OUTPUT, catalogMarkdown(catalog.source, rows, result));
  writeText(REVIEW_OUTPUT, reviewQueueMarkdown(catalog.source, rows));
  writeText(HUIJI_SOURCE_OUTPUT, huijiSourceIndexMarkdown(characterSources));
  writeText(REPORT_OUTPUT, reportMarkdown(result, characterResult));

  console.log("主线目录已写入本地知识库数据库和审核文档。");
  console.log(`目录：${CATALOG_OUTPUT}`);
  console.log(`审核队列：${REVIEW_OUTPUT}`);
} finally {
  database.close();
}

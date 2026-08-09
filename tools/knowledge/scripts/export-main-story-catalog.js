const fs = require("node:fs");
const path = require("node:path");
const {
  REPOSITORY_ROOT,
  formatDuration,
  getCatalogRows,
  getCharacterSourceRows,
  getEpisodeReviewRows,
  getMainStoryRouteComparison,
  loadMainStoryCatalog,
  openKnowledgeDatabase,
  syncExistingCharacterSources,
  syncMainStoryRouteComparison,
  syncManualStoryReviews,
  syncMainStoryCatalog,
} = require("./knowledge-db");

const CURATED_ROOT = path.join(REPOSITORY_ROOT, "knowledge", "curated");
const SOURCE_OUTPUT = path.join(CURATED_ROOT, "sources", "bilibili_main_story_BV17M4y1w7rr.md");
const CATALOG_OUTPUT = path.join(CURATED_ROOT, "videos", "main_story_catalog_v0.1.md");
const REVIEW_OUTPUT = path.join(CURATED_ROOT, "reviews", "main_story_core_01_03_review_queue_v0.1.md");
const ROUTE_COMPARISON_OUTPUT = path.join(
  CURATED_ROOT,
  "reviews",
  "main_story_2_p09_p10_route_comparison_v0.1.md"
);
const HUIJI_SOURCE_OUTPUT = path.join(CURATED_ROOT, "sources", "huiji_character_source_index_v0.1.md");
const REPORT_OUTPUT = path.join(REPOSITORY_ROOT, "reports", "knowledge_database_bootstrap_report.md");

function writeText(filePath, content) {
  fs.mkdirSync(path.dirname(filePath), { recursive: true });
  fs.writeFileSync(filePath, `${content.trim()}\n`, "utf8");
}

function formatTimecode(totalSeconds) {
  const formatted = formatDuration(totalSeconds);
  return formatted.startsWith("00:") ? formatted.slice(3) : formatted;
}

function reviewStatusLabel(status) {
  const labels = {
    context_only: "仅上下文（项目人工确认）",
    in_progress: "审核中",
    human_confirmed: "已人工确认",
    human_reviewed_structure: "结构已人工审核",
    partially_human_confirmed: "部分已人工确认",
    pending_human_confirmation: "待人工确认",
    excluded: "排除（项目人工确认）",
    not_started: "待审核",
  };
  return labels[status] || status || "待审核";
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
4. P05、P06 是第二次讨伐的区域选择分支，不属于主线本体，也不影响主线走向或结局；两条分支必须分别完整录入。
5. P07 是每个区域讨伐结束后的黑核回收后续，不是区域选择分支；各区域回收片段必须完整录入并保留其顺序。
6. P08《彩蛋——闪闪发光的迷之钥》按项目人工确认排除，不作为主线剧情采集依据。
7. 第 12 章《堕天使的挽歌》按项目编辑决定排除，不作为剧情采集依据。
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
  lines.push(`- 首批审核队列：${result.priorityCount} 集（第 1 至 3 章及其必要上下文，已排除 P08）`);
  lines.push(`- 编辑排除：${result.excludedCount} 集（P08 与第 12 章）`);
  lines.push("- 当前阶段：只完成目录与审核队列，不代表已经观看、摘要或确认全部剧情。");
  lines.push("");
  lines.push("## 分集清单");
  lines.push("");
  lines.push("| 分集 | 范围 | 标题 | 时长 | 状态 |");
  lines.push("| ---: | --- | --- | --- | --- |");

  for (const row of rows) {
    const scope = row.content_kind === "optional_branch"
      ? `区域剧情分支（关联主线 ${row.chapter_number}，不改变结局）`
      : row.content_kind === "regional_followup"
        ? `区域讨伐后续／黑核回收（关联主线 ${row.chapter_number}）`
        : row.chapter_number
      ? `主线 ${row.chapter_number}${row.chapter_label ? `：${row.chapter_label}` : ""}`
      : row.content_kind === "prologue"
        ? "引子"
        : row.content_kind === "bonus"
          ? "彩蛋"
          : "城市区段";
    const status = row.editorial_status === "excluded"
      ? "排除"
      : row.review_status !== "not_started"
        ? reviewStatusLabel(row.review_status)
        : row.priority_batch
          ? "首批待审"
          : "待审";
    lines.push(`| P${String(row.episode_no).padStart(2, "0")} | ${scope} | ${row.title} | ${row.duration_display} | ${status} |`);
  }

  lines.push("");
  lines.push("## 排除说明");
  lines.push("");
  for (const row of rows.filter((item) => item.editorial_status === "excluded")) {
    lines.push(`- P${String(row.episode_no).padStart(2, "0")}：${row.exclusion_reason}`);
  }
  return lines.join("\n");
}

function reviewQueueMarkdown(source, rows, reviewRows) {
  const lines = [];
  const reviewByEpisode = new Map(reviewRows.map((review) => [review.episode_no, review]));
  lines.push("# 第 1 至 3 章、区域选择与黑核回收人工摘要审核队列");
  lines.push("");
  lines.push(`> 视频来源：${source.id}。本队列覆盖 P01 至 P12；P05-P06 作为区域选择分支，P07 作为区域讨伐后的黑核回收流程完整收录；不自动转写，不复制完整对白。`);
  lines.push("");
  lines.push("## 使用方法");
  lines.push("");
  lines.push("1. 观看指定分集并记录最小必要时间码。\n2. 用自己的话填写剧情摘要。\n3. 将可进入知识库的事实写入候选事实栏。\n4. 人工标记“已确认 / 保留疑问 / 不采用”。\n5. 只有“已确认”事实才能迁入 curated 世界观或角色条目。");

  for (const row of rows.filter((item) => item.priority_batch === "core_chapters_01_03")) {
    const review = reviewByEpisode.get(row.episode_no);
    lines.push("");
    lines.push(`## P${String(row.episode_no).padStart(2, "0")}：${row.title}`);
    lines.push("");
    lines.push(`- 时长：${row.duration_display}`);
    const queueScope = row.content_kind === "optional_branch"
      ? `区域剧情分支（关联主线 ${row.chapter_number}，不改变结局）`
      : row.content_kind === "regional_followup"
        ? `区域讨伐后续／黑核回收（关联主线 ${row.chapter_number}）`
        : row.chapter_number
        ? `主线 ${row.chapter_number}`
        : "引子 / 上下文";
    lines.push(`- 目录定位：${queueScope}`);
    lines.push(`- 观看状态：${review?.watch_status || "未开始"}`);
    if (review?.segments?.length) {
      lines.push("- 时间码与原创摘要：");
      for (const segment of review.segments) {
        const segmentStatus = reviewStatusLabel(segment.review_status);
        lines.push(`  - ${formatTimecode(segment.start_second)}–${formatTimecode(segment.end_second)}（${segmentStatus}）：${segment.summary}`);
      }
      const facts = review.segments.flatMap((segment) => segment.candidate_facts || []);
      lines.push("- 候选事实：");
      for (const fact of facts) {
        lines.push(`  - ${fact}`);
      }
    } else {
      lines.push("- 时间码：待填写");
      lines.push("- 原创摘要：待填写");
      lines.push("- 候选事实：待填写");
    }
    lines.push(`- 与 Wiki 的关系：${review?.wiki_comparison || "待比对"}`);
    lines.push(`- 审核结果：${reviewStatusLabel(review?.review_status || row.review_status)}`);
    lines.push(`- 特殊补充：${review?.special_note || "无"}`);
  }

  const excludedPriorityRows = rows.filter(
    (item) => item.editorial_status === "excluded" && item.episode_no >= 1 && item.episode_no <= 12
  );
  if (excludedPriorityRows.length) {
    lines.push("");
    lines.push("## 本批已排除条目");
    for (const row of excludedPriorityRows) {
      const review = reviewByEpisode.get(row.episode_no);
      lines.push("");
      lines.push(`### P${String(row.episode_no).padStart(2, "0")}：${row.title}`);
      lines.push("");
      lines.push(`- 处理决定：${review?.watch_status || "排除"}`);
      lines.push(`- 排除原因：${review?.special_note || row.exclusion_reason}`);
      lines.push(`- 审核结果：${reviewStatusLabel(review?.review_status || row.review_status)}`);
    }
  }

  return lines.join("\n");
}

function comparisonClassificationLabel(classification) {
  const labels = {
    common_candidate: "共用候选",
    route_difference_candidate: "分歧候选",
    unclassified: "未分类",
  };
  return labels[classification] || classification || "未分类";
}

function comparisonEvidenceMarkdown(evidenceList) {
  if (!evidenceList.length) {
    return ["  - 暂无时间码记录"];
  }

  return evidenceList.map((evidence) => {
    const timecode = `${formatTimecode(evidence.start_second)}–${formatTimecode(evidence.end_second)}`;
    return `  - P${String(evidence.episode_no).padStart(2, "0")} ${timecode}：${evidence.note}`;
  });
}

function routeComparisonMarkdown(comparison) {
  const lines = [];
  lines.push(`# ${comparison.title}`);
  lines.push("");
  lines.push(`> 对照 ID：${comparison.comparison_id}。本文件由本地 SQLite 路线对照记录导出。`);
  lines.push(`> 审核状态：${reviewStatusLabel(comparison.review_status)}。`);
  lines.push("");
  lines.push("## 使用边界");
  lines.push("");
  lines.push(`- 范围：${comparison.scope_note}`);
  lines.push(`- 编辑说明：${comparison.editorial_note}`);
  lines.push("- 本文件不替代 P09、P10 的原始分段摘要；任何正式角色资料或世界观事实仍须回到分集、时间码和人工审核记录。");
  lines.push("");
  lines.push("## 对照项");

  for (const entry of comparison.entries) {
    lines.push("");
    lines.push(`### ${entry.comparison_no}. ${entry.topic}`);
    lines.push("");
    lines.push(`- 当前分类：${comparisonClassificationLabel(entry.classification)}（${reviewStatusLabel(entry.review_status)}）`);
    lines.push("- P09 证据：");
    lines.push(...comparisonEvidenceMarkdown(entry.p09_evidence));
    lines.push("- P10 证据：");
    lines.push(...comparisonEvidenceMarkdown(entry.p10_evidence));
    lines.push(`- 共用候选观察：${entry.shared_observation}`);
    lines.push(`- 分歧候选观察：${entry.difference_observation}`);
    lines.push("- 角色补全待办：");
    for (const followup of entry.character_followup) {
      lines.push(`  - ${followup}`);
    }
  }

  lines.push("");
  lines.push("## 人工确认后的迁入规则");
  lines.push("");
  lines.push("1. 先确认人物身份与时间线位置，再确认场景是否共通或分歧。");
  lines.push("2. 角色行动、关系、立场变化和历史处境可迁入角色档案，但必须保留分集、结局编号和时间码。");
  lines.push("3. 结局特有画面只能补充对应路线资料，不能覆盖角色共通档案或 MOD 正史。");
  lines.push("4. 任何未确认的对话、视觉效果、操作界面或片尾演出继续保留在候选层。");
  return lines.join("\n");
}

function reportMarkdown(result, characterResult, manualReviewResult, routeComparisonResult) {
  return `
# 本地知识库数据库初始化报告

- 数据库：` + "`knowledge/database/seven_days_knowledge.sqlite`" + `（本地生成，不提交二进制文件）
- 结构化视频来源记录：1
- 灰机角色来源记录：${characterResult.characterSourceCount}
- 已索引 Clean 角色文档：${characterResult.cleanCharacterCount}
- 主线视频分集记录：${result.episodeCount}
- 目录总时长：${formatDuration(result.totalDurationSeconds)}
- P08 与第 12 章排除记录：${result.excludedCount}
- 首批人工摘要队列：${result.priorityCount}
- 人工审核记录：${manualReviewResult.reviewCount}
- 已录入人工摘要时间段：${manualReviewResult.segmentCount}
- 路线对照记录：${routeComparisonResult.comparisonCount}
- 路线对照项：${routeComparisonResult.entryCount}

## 当前范围

- 已建立：来源记录、视频目录、审核状态字段、人工审核记录与时间段索引。
- 已完成首轮草稿：P01 新手引导的范围确认；P02 游戏背景主线全片的分段审核；P03 结局 1 的全片分段审核（部分已人工确认）；P04 结局 2 的全片分段审核（待人工确认）；P05 东方古街区域分支全片九段审核；P06 中央城区区域分支全片三段审核；P07 各区域讨伐结束后的黑核回收流程全片审核；P09 主线剧情 2 结局 1 全片十段审核；P10 主线剧情 2 结局 2 全片十段审核。
- 已完成路线对照：P09／P10 的共用候选、分歧候选与角色补全待办已结构化记录；所有条目仍待人工确认。
- 下一步：人工确认 P09／P10 的高优先级人物、共用节点与路线差异，再将确认事实迁入角色档案与 curated 剧情条目；同时保留 P05／P06 分歧与汇合点、P07 各区域片段对应关系和主线 1 结局线的人工补充待办。
- 未进行：视频下载、音频转写、图片下载、全站 Wiki 同步。
`;
}

const database = openKnowledgeDatabase();

try {
  const result = syncMainStoryCatalog(database);
  const manualReviewResult = syncManualStoryReviews(database);
  const routeComparisonResult = syncMainStoryRouteComparison(database);
  const characterResult = syncExistingCharacterSources(database);
  const catalog = loadMainStoryCatalog();
  const rows = getCatalogRows(database, catalog.source.id);
  const characterSources = getCharacterSourceRows(database);
  const reviewRows = getEpisodeReviewRows(database, catalog.source.id);
  const routeComparison = getMainStoryRouteComparison(
    database,
    routeComparisonResult.comparisonId
  );

  if (!routeComparison) {
    throw new Error("路线对照记录未能写入本地 SQLite 数据库。");
  }

  writeText(SOURCE_OUTPUT, sourceRecordMarkdown(catalog.source, result));
  writeText(CATALOG_OUTPUT, catalogMarkdown(catalog.source, rows, result));
  writeText(REVIEW_OUTPUT, reviewQueueMarkdown(catalog.source, rows, reviewRows));
  writeText(ROUTE_COMPARISON_OUTPUT, routeComparisonMarkdown(routeComparison));
  writeText(HUIJI_SOURCE_OUTPUT, huijiSourceIndexMarkdown(characterSources));
  writeText(
    REPORT_OUTPUT,
    reportMarkdown(result, characterResult, manualReviewResult, routeComparisonResult)
  );

  console.log("主线目录已写入本地知识库数据库和审核文档。");
  console.log(`目录：${CATALOG_OUTPUT}`);
  console.log(`审核队列：${REVIEW_OUTPUT}`);
  console.log(`路线对照：${ROUTE_COMPARISON_OUTPUT}`);
} finally {
  database.close();
}

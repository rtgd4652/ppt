const fs = require("node:fs");
const path = require("node:path");
const crypto = require("node:crypto");
const { DatabaseSync } = require("node:sqlite");

// 本工具只维护知识库的本地结构化索引，不接触 Stellaris 的 mod/ 运行目录。
const REPOSITORY_ROOT = path.resolve(__dirname, "..", "..", "..");
const DATABASE_DIR = path.join(REPOSITORY_ROOT, "knowledge", "database");
const DATABASE_PATH = path.join(DATABASE_DIR, "seven_days_knowledge.sqlite");
const MAIN_STORY_CATALOG_PATH = path.join(
  REPOSITORY_ROOT,
  "tools",
  "knowledge",
  "data",
  "bilibili_main_story_BV17M4y1w7rr.json"
);
const MAIN_STORY_MANUAL_REVIEW_PATH = path.join(
  REPOSITORY_ROOT,
  "tools",
  "knowledge",
  "data",
  "main_story_manual_reviews_v0.1.json"
);
const MAIN_STORY_ROUTE_COMPARISON_PATH = path.join(
  REPOSITORY_ROOT,
  "tools",
  "knowledge",
  "data",
  "main_story_route_comparisons_v0.1.json"
);
const CLEAN_CHARACTER_DIR = path.join(REPOSITORY_ROOT, "knowledge", "characters");

function openKnowledgeDatabase() {
  fs.mkdirSync(DATABASE_DIR, { recursive: true });
  const database = new DatabaseSync(DATABASE_PATH);
  database.exec("PRAGMA foreign_keys = ON;");
  ensureSchema(database);
  return database;
}

function ensureSchema(database) {
  // 来源表保存页面、视频或人工确认资料的身份与使用边界。
  database.exec(`
    CREATE TABLE IF NOT EXISTS source_records (
      source_id TEXT PRIMARY KEY,
      provider TEXT NOT NULL,
      source_type TEXT NOT NULL,
      title TEXT NOT NULL,
      canonical_url TEXT NOT NULL,
      uploader TEXT,
      published_on TEXT,
      source_scope TEXT NOT NULL,
      project_authority TEXT NOT NULL,
      coverage_note TEXT NOT NULL,
      imported_at TEXT NOT NULL,
      updated_at TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS video_episodes (
      source_id TEXT NOT NULL,
      episode_no INTEGER NOT NULL,
      title TEXT NOT NULL,
      duration_seconds INTEGER NOT NULL,
      duration_display TEXT NOT NULL,
      content_kind TEXT NOT NULL,
      chapter_number INTEGER,
      chapter_label TEXT,
      ending_code INTEGER,
      ending_title TEXT,
      route_note TEXT,
      editorial_status TEXT NOT NULL,
      priority_batch TEXT,
      exclusion_reason TEXT,
      review_status TEXT NOT NULL,
      created_at TEXT NOT NULL,
      updated_at TEXT NOT NULL,
      PRIMARY KEY (source_id, episode_no),
      FOREIGN KEY (source_id) REFERENCES source_records(source_id)
    );

    CREATE TABLE IF NOT EXISTS episode_reviews (
      source_id TEXT NOT NULL,
      episode_no INTEGER NOT NULL,
      watch_status TEXT NOT NULL,
      review_status TEXT NOT NULL,
      wiki_comparison TEXT NOT NULL,
      special_note TEXT NOT NULL,
      created_at TEXT NOT NULL,
      updated_at TEXT NOT NULL,
      PRIMARY KEY (source_id, episode_no),
      FOREIGN KEY (source_id, episode_no) REFERENCES video_episodes(source_id, episode_no)
    );

    CREATE TABLE IF NOT EXISTS episode_review_segments (
      source_id TEXT NOT NULL,
      episode_no INTEGER NOT NULL,
      segment_no INTEGER NOT NULL,
      start_second INTEGER NOT NULL,
      end_second INTEGER NOT NULL,
      summary TEXT NOT NULL,
      candidate_facts_json TEXT NOT NULL,
      review_status TEXT NOT NULL,
      created_at TEXT NOT NULL,
      updated_at TEXT NOT NULL,
      PRIMARY KEY (source_id, episode_no, segment_no),
      FOREIGN KEY (source_id, episode_no) REFERENCES video_episodes(source_id, episode_no)
    );

    CREATE TABLE IF NOT EXISTS route_comparisons (
      comparison_id TEXT PRIMARY KEY,
      source_id TEXT NOT NULL,
      title TEXT NOT NULL,
      review_status TEXT NOT NULL,
      scope_note TEXT NOT NULL,
      editorial_note TEXT NOT NULL,
      created_at TEXT NOT NULL,
      updated_at TEXT NOT NULL,
      FOREIGN KEY (source_id) REFERENCES source_records(source_id)
    );

    CREATE TABLE IF NOT EXISTS route_comparison_entries (
      comparison_id TEXT NOT NULL,
      comparison_no INTEGER NOT NULL,
      topic TEXT NOT NULL,
      classification TEXT NOT NULL,
      p09_evidence_json TEXT NOT NULL,
      p10_evidence_json TEXT NOT NULL,
      shared_observation TEXT NOT NULL,
      difference_observation TEXT NOT NULL,
      character_followup_json TEXT NOT NULL,
      review_status TEXT NOT NULL,
      created_at TEXT NOT NULL,
      updated_at TEXT NOT NULL,
      PRIMARY KEY (comparison_id, comparison_no),
      FOREIGN KEY (comparison_id) REFERENCES route_comparisons(comparison_id)
    );

    CREATE TABLE IF NOT EXISTS glossary_terms (
      term_id TEXT PRIMARY KEY,
      title TEXT NOT NULL,
      domain TEXT NOT NULL,
      knowledge_layer TEXT NOT NULL DEFAULT 'original_fact',
      review_status TEXT NOT NULL,
      canonical_summary TEXT,
      usage_note TEXT NOT NULL DEFAULT '',
      manifest_id TEXT NOT NULL DEFAULT '',
      sort_order INTEGER NOT NULL DEFAULT 0,
      notes TEXT NOT NULL DEFAULT '',
      created_at TEXT NOT NULL,
      updated_at TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS glossary_aliases (
      term_id TEXT NOT NULL,
      alias TEXT NOT NULL,
      alias_type TEXT NOT NULL DEFAULT 'alias',
      notes TEXT NOT NULL DEFAULT '',
      PRIMARY KEY (term_id, alias),
      FOREIGN KEY (term_id) REFERENCES glossary_terms(term_id) ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS glossary_term_references (
      reference_id TEXT PRIMARY KEY,
      term_id TEXT NOT NULL,
      reference_no INTEGER NOT NULL,
      reference_type TEXT NOT NULL,
      source_locator TEXT NOT NULL,
      source_id TEXT,
      document_id TEXT,
      source_section TEXT,
      evidence_role TEXT NOT NULL,
      review_status TEXT NOT NULL,
      notes TEXT NOT NULL DEFAULT '',
      FOREIGN KEY (term_id) REFERENCES glossary_terms(term_id) ON DELETE CASCADE,
      FOREIGN KEY (source_id) REFERENCES source_records(source_id),
      FOREIGN KEY (document_id) REFERENCES knowledge_documents(document_id)
    );

    CREATE TABLE IF NOT EXISTS glossary_relations (
      term_id TEXT NOT NULL,
      related_term_id TEXT NOT NULL,
      relation_type TEXT NOT NULL,
      notes TEXT NOT NULL DEFAULT '',
      PRIMARY KEY (term_id, related_term_id, relation_type),
      FOREIGN KEY (term_id) REFERENCES glossary_terms(term_id) ON DELETE CASCADE,
      FOREIGN KEY (related_term_id) REFERENCES glossary_terms(term_id)
    );

    CREATE TABLE IF NOT EXISTS knowledge_documents (
      document_id TEXT PRIMARY KEY,
      document_type TEXT NOT NULL,
      layer TEXT NOT NULL,
      title TEXT NOT NULL,
      file_path TEXT NOT NULL UNIQUE,
      source_id TEXT,
      last_sync TEXT,
      document_status TEXT NOT NULL,
      indexed_at TEXT NOT NULL,
      updated_at TEXT NOT NULL,
      FOREIGN KEY (source_id) REFERENCES source_records(source_id)
    );

    CREATE TABLE IF NOT EXISTS claims (
      claim_id TEXT PRIMARY KEY,
      domain TEXT NOT NULL,
      subject TEXT NOT NULL,
      statement TEXT NOT NULL,
      claim_type TEXT NOT NULL,
      review_status TEXT NOT NULL,
      reviewer TEXT,
      reviewed_at TEXT,
      notes TEXT,
      created_at TEXT NOT NULL,
      updated_at TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS claim_evidence (
      evidence_id TEXT PRIMARY KEY,
      claim_id TEXT NOT NULL,
      source_id TEXT NOT NULL,
      episode_no INTEGER,
      source_section TEXT,
      start_second INTEGER,
      end_second INTEGER,
      short_quote TEXT,
      evidence_note TEXT,
      created_at TEXT NOT NULL,
      FOREIGN KEY (claim_id) REFERENCES claims(claim_id),
      FOREIGN KEY (source_id) REFERENCES source_records(source_id)
    );

    CREATE TABLE IF NOT EXISTS review_log (
      review_id TEXT PRIMARY KEY,
      record_type TEXT NOT NULL,
      record_id TEXT NOT NULL,
      decision TEXT NOT NULL,
      reviewer TEXT,
      note TEXT,
      reviewed_at TEXT NOT NULL
    );
  `);

  // 旧数据库中已经存在精简版 glossary_terms。这里采用幂等增列迁移，
  // 不重建数据库，也不触碰既有剧情、角色、事实或证据记录。
  const glossaryColumns = database
    .prepare("PRAGMA table_info(glossary_terms)")
    .all()
    .map((column) => column.name);
  const glossaryMigrations = [
    ["knowledge_layer", "TEXT NOT NULL DEFAULT 'original_fact'"],
    ["usage_note", "TEXT NOT NULL DEFAULT ''"],
    ["manifest_id", "TEXT NOT NULL DEFAULT ''"],
    ["sort_order", "INTEGER NOT NULL DEFAULT 0"],
    ["notes", "TEXT NOT NULL DEFAULT ''"],
  ];
  for (const [columnName, definition] of glossaryMigrations) {
    if (!glossaryColumns.includes(columnName)) {
      database.exec(`ALTER TABLE glossary_terms ADD COLUMN ${columnName} ${definition};`);
    }
  }

  database.exec(`
    CREATE INDEX IF NOT EXISTS idx_glossary_terms_manifest
      ON glossary_terms(manifest_id, sort_order, title);
    CREATE INDEX IF NOT EXISTS idx_glossary_references_term
      ON glossary_term_references(term_id, reference_no);
    CREATE INDEX IF NOT EXISTS idx_glossary_relations_related
      ON glossary_relations(related_term_id);
  `);
}

function loadMainStoryCatalog() {
  return JSON.parse(fs.readFileSync(MAIN_STORY_CATALOG_PATH, "utf8"));
}

function loadMainStoryManualReviews() {
  // 人工审核草稿单独存放，避免自动目录采集覆盖人工填写的摘要与排除决定。
  return JSON.parse(fs.readFileSync(MAIN_STORY_MANUAL_REVIEW_PATH, "utf8"));
}

function loadMainStoryRouteComparison() {
  // 路线对照种子只保存人工审核前的结构性候选，不替代原分集摘要或事实卡。
  return JSON.parse(fs.readFileSync(MAIN_STORY_ROUTE_COMPARISON_PATH, "utf8"));
}

function parseDuration(durationText) {
  const parts = String(durationText)
    .trim()
    .split(":")
    .map((value) => Number.parseInt(value, 10));

  if (!parts.length || parts.some((value) => Number.isNaN(value))) {
    throw new Error(`无法解析视频时长：${durationText}`);
  }

  return parts.reduce((total, value) => total * 60 + value, 0);
}

function formatDuration(totalSeconds) {
  const seconds = Math.max(0, Number(totalSeconds) || 0);
  const hours = Math.floor(seconds / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  const restSeconds = seconds % 60;

  return `${String(hours).padStart(2, "0")}:${String(minutes).padStart(2, "0")}:${String(restSeconds).padStart(2, "0")}`;
}

function stableId(prefix, value) {
  const digest = crypto.createHash("sha1").update(String(value)).digest("hex").slice(0, 12).toUpperCase();
  return `${prefix}-${digest}`;
}

function parseCleanCharacterFrontmatter(markdown) {
  const frontmatter = /^---\r?\n([\s\S]*?)\r?\n---/.exec(markdown)?.[1] || "";
  const readValue = (key) => {
    const match = new RegExp(`^${key}:\\s*[\"]?(.+?)[\"]?\\s*$`, "m").exec(frontmatter);
    return match ? match[1].trim().replace(/^"|"$/g, "") : "";
  };

  return {
    title: readValue("title"),
    lastSync: readValue("last_sync"),
    sourceUrl: /^- 来源页面：(https?:\/\/\S+)/m.exec(markdown)?.[1] || "",
  };
}

function listCleanCharacterFiles() {
  // 只把自动采集后的 clean 角色资料纳入来源索引，排除标准角色档案与关系文档。
  return fs
    .readdirSync(CLEAN_CHARACTER_DIR, { withFileTypes: true })
    .filter((entry) => entry.isFile() && entry.name.endsWith(".md"))
    .map((entry) => entry.name)
    .filter((name) => !name.includes("_character_") && !name.startsWith("character_"));
}

function syncExistingCharacterSources(database) {
  const timestamp = new Date().toISOString();
  const files = listCleanCharacterFiles();

  const upsertSource = database.prepare(`
    INSERT INTO source_records (
      source_id, provider, source_type, title, canonical_url, uploader, published_on,
      source_scope, project_authority, coverage_note, imported_at, updated_at
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ON CONFLICT(source_id) DO UPDATE SET
      provider = excluded.provider,
      source_type = excluded.source_type,
      title = excluded.title,
      canonical_url = excluded.canonical_url,
      source_scope = excluded.source_scope,
      project_authority = excluded.project_authority,
      coverage_note = excluded.coverage_note,
      updated_at = excluded.updated_at
  `);
  const upsertDocument = database.prepare(`
    INSERT INTO knowledge_documents (
      document_id, document_type, layer, title, file_path, source_id,
      last_sync, document_status, indexed_at, updated_at
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ON CONFLICT(file_path) DO UPDATE SET
      title = excluded.title,
      source_id = excluded.source_id,
      last_sync = excluded.last_sync,
      document_status = excluded.document_status,
      updated_at = excluded.updated_at
  `);

  database.exec("BEGIN IMMEDIATE;");
  try {
    for (const filename of files) {
      const fullPath = path.join(CLEAN_CHARACTER_DIR, filename);
      const metadata = parseCleanCharacterFrontmatter(fs.readFileSync(fullPath, "utf8"));
      if (!metadata.title || !metadata.sourceUrl) {
        continue;
      }

      const sourceId = stableId("SRC-HUIJI-CHAR", metadata.title);
      const relativePath = path.relative(REPOSITORY_ROOT, fullPath).split(path.sep).join("/");
      upsertSource.run(
        sourceId,
        "Huiji Wiki",
        "wiki_page",
        metadata.title,
        metadata.sourceUrl,
        "",
        "",
        "角色 clean 资料的基础事实来源；页面内容仍需逐条人工审核。",
        "角色基础资料证据（需人工审核）",
        "对应 raw Markdown、图片索引和 Mod Ready 摘要均保留在本地仓库。",
        timestamp,
        timestamp
      );
      upsertDocument.run(
        stableId("DOC-CLEAN-CHAR", relativePath),
        "character",
        "clean",
        metadata.title,
        relativePath,
        sourceId,
        metadata.lastSync,
        "collected",
        timestamp,
        timestamp
      );
    }
    database.exec("COMMIT;");
  } catch (error) {
    database.exec("ROLLBACK;");
    throw error;
  }

  return {
    // 灰机 Wiki 的剧情页与角色页使用相同 provider/source_type，必须按 Clean 角色文档关系计数。
    characterSourceCount: getCharacterSourceRows(database).length,
    cleanCharacterCount: database
      .prepare("SELECT COUNT(*) AS count FROM knowledge_documents WHERE document_type = ? AND layer = ?")
      .get("character", "clean").count,
  };
}

function extractRouteNote(title) {
  const notes = [];
  for (const match of String(title).matchAll(/（([^）]+)）/g)) {
    notes.push(match[1].trim());
  }
  return notes.join("；");
}

function deriveEpisodeMetadata(episode, editorialRules = {}) {
  const title = String(episode.title).trim();
  const mainStory = /^主线剧情(\d+)([^—]*)——结局(\d+)：(.+)$/.exec(title);
  // 区域选择与讨伐后续分别由目录规则维护，避免把 P05-P07 误归类为主线本体或同一种分支。
  const optionalBranchParentChapters = editorialRules.optional_branch_parent_chapters || {};
  const configuredOptionalBranchChapter = optionalBranchParentChapters[String(episode.page)];
  const optionalBranchChapter = Number.isInteger(configuredOptionalBranchChapter)
    ? configuredOptionalBranchChapter
    : null;
  const regionalFollowupParentChapters = editorialRules.regional_followup_parent_chapters || {};
  const configuredRegionalFollowupChapter = regionalFollowupParentChapters[String(episode.page)];
  const regionalFollowupChapter = Number.isInteger(configuredRegionalFollowupChapter)
    ? configuredRegionalFollowupChapter
    : null;
  const cityInterludeChapter = episode.page >= 51 && episode.page <= 52 ? 18 : null;
  const isBonus = title.startsWith("彩蛋");
  const isOptionalBranch = optionalBranchChapter !== null;
  const isRegionalFollowup = regionalFollowupChapter !== null;
  const isCityInterlude =
    !isOptionalBranch &&
    !isRegionalFollowup &&
    (title.startsWith("城市区域讨伐剧情") || title.startsWith("城市黑核回收剧情"));
  const chapterNumber = mainStory
    ? Number.parseInt(mainStory[1], 10)
    : isOptionalBranch
      ? optionalBranchChapter
      : isRegionalFollowup
        ? regionalFollowupChapter
        : cityInterludeChapter;
  const excludedChapters = editorialRules.excluded_chapters || [];
  const excludedEpisodePages = editorialRules.excluded_episode_pages || [];
  const chapterExcluded = chapterNumber !== null && excludedChapters.includes(chapterNumber);
  const episodeExcluded = excludedEpisodePages.includes(episode.page);
  const excluded = chapterExcluded || episodeExcluded;
  const priorityRange = editorialRules.priority_episode_range || [];
  const inPriorityRange =
    priorityRange.length === 2 && episode.page >= priorityRange[0] && episode.page <= priorityRange[1];
  const exclusionReason = chapterExcluded
    ? "项目编辑决定：第 12 章《堕天使的挽歌》不进入知识采集与世界观依据。"
    : episodeExcluded
      ? "项目人工确认：P08《彩蛋——闪闪发光的迷之钥》不进入主线剧情采集、摘要、事实提取或世界观引用。"
      : "";
  const baseRouteNote = extractRouteNote(title);
  const optionalBranchNote = editorialRules.optional_branch_note || "";
  const regionalFollowupNote = editorialRules.regional_followup_note || "";

  return {
    durationSeconds: parseDuration(episode.duration),
    contentKind: mainStory
      ? "main_story"
      : isOptionalBranch
        ? "optional_branch"
        : isRegionalFollowup
          ? "regional_followup"
          : isCityInterlude
            ? "city_interlude"
            : isBonus
              ? "bonus"
              : "prologue",
    chapterNumber,
    chapterLabel: mainStory
      ? mainStory[2].trim()
      : isOptionalBranch
        ? "中段区域剧情分支"
        : isRegionalFollowup
          ? "区域讨伐后续 / 黑核回收"
          : isCityInterlude
            ? "城市区段 / 黑核回收"
            : "",
    endingCode: mainStory ? Number.parseInt(mainStory[3], 10) : null,
    endingTitle: mainStory ? mainStory[4].trim() : "",
    routeNote: isOptionalBranch
      ? [baseRouteNote, optionalBranchNote].filter(Boolean).join("；")
      : isRegionalFollowup
        ? [baseRouteNote, regionalFollowupNote].filter(Boolean).join("；")
        : baseRouteNote,
    editorialStatus: excluded ? "excluded" : "queued",
    priorityBatch: inPriorityRange && !excluded ? editorialRules.priority_batch || "" : "",
    exclusionReason,
    reviewStatus: excluded ? "excluded" : "not_started",
  };
}

function syncMainStoryCatalog(database) {
  const catalog = loadMainStoryCatalog();
  const timestamp = new Date().toISOString();

  const upsertSource = database.prepare(`
    INSERT INTO source_records (
      source_id, provider, source_type, title, canonical_url, uploader, published_on,
      source_scope, project_authority, coverage_note, imported_at, updated_at
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ON CONFLICT(source_id) DO UPDATE SET
      provider = excluded.provider,
      source_type = excluded.source_type,
      title = excluded.title,
      canonical_url = excluded.canonical_url,
      uploader = excluded.uploader,
      published_on = excluded.published_on,
      source_scope = excluded.source_scope,
      project_authority = excluded.project_authority,
      coverage_note = excluded.coverage_note,
      updated_at = excluded.updated_at
  `);

  const upsertEpisode = database.prepare(`
    INSERT INTO video_episodes (
      source_id, episode_no, title, duration_seconds, duration_display, content_kind,
      chapter_number, chapter_label, ending_code, ending_title, route_note,
      editorial_status, priority_batch, exclusion_reason, review_status, created_at, updated_at
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ON CONFLICT(source_id, episode_no) DO UPDATE SET
      title = excluded.title,
      duration_seconds = excluded.duration_seconds,
      duration_display = excluded.duration_display,
      content_kind = excluded.content_kind,
      chapter_number = excluded.chapter_number,
      chapter_label = excluded.chapter_label,
      ending_code = excluded.ending_code,
      ending_title = excluded.ending_title,
      route_note = excluded.route_note,
      editorial_status = excluded.editorial_status,
      priority_batch = excluded.priority_batch,
      exclusion_reason = excluded.exclusion_reason,
      review_status = excluded.review_status,
      updated_at = excluded.updated_at
  `);

  database.exec("BEGIN IMMEDIATE;");
  try {
    upsertSource.run(
      catalog.source.id,
      catalog.source.provider,
      catalog.source.type,
      catalog.source.title,
      catalog.source.url,
      catalog.source.uploader,
      catalog.source.published_on,
      catalog.source.scope,
      catalog.source.project_authority,
      catalog.source.coverage_note,
      timestamp,
      timestamp
    );

    for (const episode of catalog.episodes) {
      const metadata = deriveEpisodeMetadata(episode, catalog.editorial_rules || {});
      upsertEpisode.run(
        catalog.source.id,
        episode.page,
        episode.title,
        metadata.durationSeconds,
        episode.duration,
        metadata.contentKind,
        metadata.chapterNumber,
        metadata.chapterLabel,
        metadata.endingCode,
        metadata.endingTitle,
        metadata.routeNote,
        metadata.editorialStatus,
        metadata.priorityBatch,
        metadata.exclusionReason,
        metadata.reviewStatus,
        timestamp,
        timestamp
      );
    }

    database.exec("COMMIT;");
  } catch (error) {
    database.exec("ROLLBACK;");
    throw error;
  }

  const rows = database
    .prepare("SELECT duration_seconds, editorial_status, priority_batch FROM video_episodes WHERE source_id = ?")
    .all(catalog.source.id);

  return {
    sourceId: catalog.source.id,
    episodeCount: rows.length,
    totalDurationSeconds: rows.reduce((total, row) => total + row.duration_seconds, 0),
    excludedCount: rows.filter((row) => row.editorial_status === "excluded").length,
    priorityCount: rows.filter((row) => row.priority_batch === "core_chapters_01_03").length,
  };
}

function syncManualStoryReviews(database) {
  // 审核种子保存用户确认与人工摘要草稿；先同步目录，才能保证外键指向真实分集。
  const reviewData = loadMainStoryManualReviews();
  const timestamp = new Date().toISOString();
  const sourceId = reviewData.source_id;

  if (!sourceId) {
    throw new Error("人工审核种子缺少 source_id。");
  }

  const sourceExists = database.prepare("SELECT source_id FROM source_records WHERE source_id = ?").get(sourceId);
  if (!sourceExists) {
    throw new Error(`人工审核来源尚未导入：${sourceId}`);
  }

  const upsertReview = database.prepare(`
    INSERT INTO episode_reviews (
      source_id, episode_no, watch_status, review_status, wiki_comparison,
      special_note, created_at, updated_at
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ON CONFLICT(source_id, episode_no) DO UPDATE SET
      watch_status = excluded.watch_status,
      review_status = excluded.review_status,
      wiki_comparison = excluded.wiki_comparison,
      special_note = excluded.special_note,
      updated_at = excluded.updated_at
  `);
  const deleteSegments = database.prepare(
    "DELETE FROM episode_review_segments WHERE source_id = ? AND episode_no = ?"
  );
  const insertSegment = database.prepare(`
    INSERT INTO episode_review_segments (
      source_id, episode_no, segment_no, start_second, end_second,
      summary, candidate_facts_json, review_status, created_at, updated_at
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
  `);
  const updateEpisodeReviewStatus = database.prepare(
    "UPDATE video_episodes SET review_status = ?, updated_at = ? WHERE source_id = ? AND episode_no = ?"
  );
  const episodeExists = database.prepare(
    "SELECT episode_no FROM video_episodes WHERE source_id = ? AND episode_no = ?"
  );

  database.exec("BEGIN IMMEDIATE;");
  try {
    for (const review of reviewData.reviews || []) {
      const episodeNo = Number(review.episode_no);
      if (!Number.isInteger(episodeNo) || !episodeExists.get(sourceId, episodeNo)) {
        throw new Error(`人工审核引用了不存在的分集：P${review.episode_no}`);
      }

      upsertReview.run(
        sourceId,
        episodeNo,
        review.watch_status || "未开始",
        review.review_status || "not_started",
        review.wiki_comparison || "待比对",
        review.special_note || "无",
        timestamp,
        timestamp
      );
      deleteSegments.run(sourceId, episodeNo);

      for (const segment of review.segments || []) {
        const startSecond = Number(segment.start_second);
        const endSecond = Number(segment.end_second);
        if (!Number.isFinite(startSecond) || !Number.isFinite(endSecond) || endSecond < startSecond) {
          throw new Error(`P${episodeNo} 的人工摘要时间码无效。`);
        }

        insertSegment.run(
          sourceId,
          episodeNo,
          Number(segment.segment_no),
          startSecond,
          endSecond,
          segment.summary || "待填写",
          JSON.stringify(segment.candidate_facts || []),
          segment.review_status || review.review_status || "not_started",
          timestamp,
          timestamp
        );
      }

      updateEpisodeReviewStatus.run(review.review_status || "not_started", timestamp, sourceId, episodeNo);
    }
    database.exec("COMMIT;");
  } catch (error) {
    database.exec("ROLLBACK;");
    throw error;
  }

  return {
    sourceId,
    reviewCount: database.prepare("SELECT COUNT(*) AS count FROM episode_reviews WHERE source_id = ?").get(sourceId).count,
    segmentCount: database
      .prepare("SELECT COUNT(*) AS count FROM episode_review_segments WHERE source_id = ?")
      .get(sourceId).count,
  };
}

function syncMainStoryRouteComparison(database) {
  // 路线对照独立于分集摘要：它只整理 P09／P10 的候选结构，不创建正式剧情事实。
  const comparison = loadMainStoryRouteComparison();
  const timestamp = new Date().toISOString();

  if (!comparison.comparison_id || !comparison.source_id) {
    throw new Error("路线对照种子缺少 comparison_id 或 source_id。");
  }

  const sourceExists = database
    .prepare("SELECT source_id FROM source_records WHERE source_id = ?")
    .get(comparison.source_id);
  if (!sourceExists) {
    throw new Error(`路线对照来源尚未导入：${comparison.source_id}`);
  }

  const episodeExists = database.prepare(
    "SELECT episode_no FROM video_episodes WHERE source_id = ? AND episode_no = ?"
  );
  const upsertComparison = database.prepare(`
    INSERT INTO route_comparisons (
      comparison_id, source_id, title, review_status, scope_note, editorial_note,
      created_at, updated_at
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ON CONFLICT(comparison_id) DO UPDATE SET
      source_id = excluded.source_id,
      title = excluded.title,
      review_status = excluded.review_status,
      scope_note = excluded.scope_note,
      editorial_note = excluded.editorial_note,
      updated_at = excluded.updated_at
  `);
  const deleteEntries = database.prepare(
    "DELETE FROM route_comparison_entries WHERE comparison_id = ?"
  );
  const insertEntry = database.prepare(`
    INSERT INTO route_comparison_entries (
      comparison_id, comparison_no, topic, classification, p09_evidence_json,
      p10_evidence_json, shared_observation, difference_observation,
      character_followup_json, review_status, created_at, updated_at
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
  `);

  database.exec("BEGIN IMMEDIATE;");
  try {
    upsertComparison.run(
      comparison.comparison_id,
      comparison.source_id,
      comparison.title || "未命名路线对照",
      comparison.review_status || "pending_human_confirmation",
      comparison.scope_note || "待补充",
      comparison.editorial_note || "待补充",
      timestamp,
      timestamp
    );
    deleteEntries.run(comparison.comparison_id);

    for (const entry of comparison.entries || []) {
      const comparisonNo = Number(entry.comparison_no);
      if (!Number.isInteger(comparisonNo) || comparisonNo <= 0) {
        throw new Error("路线对照项缺少有效 comparison_no。");
      }

      const p09Evidence = Array.isArray(entry.p09_evidence) ? entry.p09_evidence : [];
      const p10Evidence = Array.isArray(entry.p10_evidence) ? entry.p10_evidence : [];
      for (const evidence of [...p09Evidence, ...p10Evidence]) {
        const episodeNo = Number(evidence.episode_no);
        if (!Number.isInteger(episodeNo) || !episodeExists.get(comparison.source_id, episodeNo)) {
          throw new Error(`路线对照项 ${comparisonNo} 引用了不存在的分集。`);
        }
      }

      insertEntry.run(
        comparison.comparison_id,
        comparisonNo,
        entry.topic || "未命名对照项",
        entry.classification || "unclassified",
        JSON.stringify(p09Evidence),
        JSON.stringify(p10Evidence),
        entry.shared_observation || "待人工确认",
        entry.difference_observation || "待人工确认",
        JSON.stringify(Array.isArray(entry.character_followup) ? entry.character_followup : []),
        entry.review_status || comparison.review_status || "pending_human_confirmation",
        timestamp,
        timestamp
      );
    }
    database.exec("COMMIT;");
  } catch (error) {
    database.exec("ROLLBACK;");
    throw error;
  }

  return {
    comparisonId: comparison.comparison_id,
    comparisonCount: database.prepare("SELECT COUNT(*) AS count FROM route_comparisons").get().count,
    entryCount: database
      .prepare("SELECT COUNT(*) AS count FROM route_comparison_entries WHERE comparison_id = ?")
      .get(comparison.comparison_id).count,
  };
}

function getMainStoryRouteComparison(database, comparisonId) {
  const comparison = database.prepare(`
    SELECT comparison_id, source_id, title, review_status, scope_note, editorial_note
    FROM route_comparisons
    WHERE comparison_id = ?
  `).get(comparisonId);

  if (!comparison) {
    return null;
  }

  const entries = database.prepare(`
    SELECT
      comparison_no, topic, classification, p09_evidence_json, p10_evidence_json,
      shared_observation, difference_observation, character_followup_json, review_status
    FROM route_comparison_entries
    WHERE comparison_id = ?
    ORDER BY comparison_no
  `).all(comparisonId).map((entry) => ({
    ...entry,
    p09_evidence: JSON.parse(entry.p09_evidence_json || "[]"),
    p10_evidence: JSON.parse(entry.p10_evidence_json || "[]"),
    character_followup: JSON.parse(entry.character_followup_json || "[]"),
  }));

  return {
    ...comparison,
    entries,
  };
}

function getEpisodeReviewRows(database, sourceId) {
  const reviews = database
    .prepare(`
      SELECT episode_no, watch_status, review_status, wiki_comparison, special_note
      FROM episode_reviews
      WHERE source_id = ?
      ORDER BY episode_no
    `)
    .all(sourceId);
  const segments = database.prepare(`
    SELECT segment_no, start_second, end_second, summary, candidate_facts_json, review_status
    FROM episode_review_segments
    WHERE source_id = ? AND episode_no = ?
    ORDER BY segment_no
  `);

  return reviews.map((review) => ({
    ...review,
    segments: segments.all(sourceId, review.episode_no).map((segment) => ({
      ...segment,
      candidate_facts: JSON.parse(segment.candidate_facts_json || "[]"),
    })),
  }));
}

function getConfiguredExcludedEpisodePages(catalog) {
  // 用同一套规则推导排除分集，避免校验逻辑与目录导入逻辑出现两个真相来源。
  return catalog.episodes
    .filter((episode) => deriveEpisodeMetadata(episode, catalog.editorial_rules || {}).editorialStatus === "excluded")
    .map((episode) => episode.page)
    .sort((left, right) => left - right);
}

function getCatalogRows(database, sourceId) {
  return database
    .prepare(`
      SELECT
        episode_no, title, duration_seconds, duration_display, content_kind,
        chapter_number, chapter_label, ending_code, ending_title, route_note,
        editorial_status, priority_batch, exclusion_reason, review_status
      FROM video_episodes
      WHERE source_id = ?
      ORDER BY episode_no
    `)
    .all(sourceId);
}

function getCharacterSourceRows(database) {
  return database
    .prepare(`
      SELECT DISTINCT source.source_id, source.title, source.canonical_url
      FROM source_records AS source
      INNER JOIN knowledge_documents AS document
        ON document.source_id = source.source_id
      WHERE source.provider = ?
        AND source.source_type = ?
        AND document.document_type = ?
        AND document.layer = ?
      ORDER BY source.title
    `)
    .all("Huiji Wiki", "wiki_page", "character", "clean");
}

module.exports = {
  DATABASE_PATH,
  REPOSITORY_ROOT,
  formatDuration,
  getCatalogRows,
  getCharacterSourceRows,
  getConfiguredExcludedEpisodePages,
  getEpisodeReviewRows,
  getMainStoryRouteComparison,
  listCleanCharacterFiles,
  loadMainStoryCatalog,
  loadMainStoryManualReviews,
  loadMainStoryRouteComparison,
  openKnowledgeDatabase,
  syncExistingCharacterSources,
  syncMainStoryRouteComparison,
  syncManualStoryReviews,
  syncMainStoryCatalog,
};

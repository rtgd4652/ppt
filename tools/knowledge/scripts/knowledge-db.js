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

    CREATE TABLE IF NOT EXISTS glossary_terms (
      term_id TEXT PRIMARY KEY,
      title TEXT NOT NULL,
      domain TEXT NOT NULL,
      review_status TEXT NOT NULL,
      canonical_summary TEXT,
      created_at TEXT NOT NULL,
      updated_at TEXT NOT NULL
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
}

function loadMainStoryCatalog() {
  return JSON.parse(fs.readFileSync(MAIN_STORY_CATALOG_PATH, "utf8"));
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

function syncExistingCharacterSources(database) {
  const timestamp = new Date().toISOString();
  const files = fs
    .readdirSync(CLEAN_CHARACTER_DIR, { withFileTypes: true })
    .filter((entry) => entry.isFile() && entry.name.endsWith(".md"))
    .map((entry) => entry.name)
    .filter((name) => !name.includes("_character_") && !name.startsWith("character_"));

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
    characterSourceCount: database.prepare("SELECT COUNT(*) AS count FROM source_records WHERE provider = ?").get("Huiji Wiki").count,
    cleanCharacterCount: database.prepare("SELECT COUNT(*) AS count FROM knowledge_documents WHERE layer = ?").get("clean").count,
  };
}

function extractRouteNote(title) {
  const notes = [];
  for (const match of String(title).matchAll(/（([^）]+)）/g)) {
    notes.push(match[1].trim());
  }
  return notes.join("；");
}

function deriveEpisodeMetadata(episode, excludedChapters) {
  const title = String(episode.title).trim();
  const mainStory = /^主线剧情(\d+)([^—]*)——结局(\d+)：(.+)$/.exec(title);
  const cityInterludeChapter =
    episode.page >= 5 && episode.page <= 8 ? 1 : episode.page >= 51 && episode.page <= 52 ? 18 : null;
  const isBonus = title.startsWith("彩蛋");
  const isCityInterlude = title.startsWith("城市区域讨伐剧情") || title.startsWith("城市黑核回收剧情");
  const chapterNumber = mainStory ? Number.parseInt(mainStory[1], 10) : cityInterludeChapter;
  const excluded = chapterNumber !== null && excludedChapters.includes(chapterNumber);

  return {
    durationSeconds: parseDuration(episode.duration),
    contentKind: mainStory ? "main_story" : isCityInterlude ? "city_interlude" : isBonus ? "bonus" : "prologue",
    chapterNumber,
    chapterLabel: mainStory ? mainStory[2].trim() : isCityInterlude ? "城市区段 / 黑核回收" : "",
    endingCode: mainStory ? Number.parseInt(mainStory[3], 10) : null,
    endingTitle: mainStory ? mainStory[4].trim() : "",
    routeNote: extractRouteNote(title),
    editorialStatus: excluded ? "excluded" : "queued",
    priorityBatch: episode.page >= 1 && episode.page <= 12 ? "core_chapters_01_03" : "",
    exclusionReason: excluded ? "项目编辑决定：第 12 章《堕天使的挽歌》不进入知识采集与世界观依据。" : "",
    reviewStatus: excluded ? "excluded" : "not_started",
  };
}

function syncMainStoryCatalog(database) {
  const catalog = loadMainStoryCatalog();
  const timestamp = new Date().toISOString();
  const excludedChapters = catalog.editorial_rules?.excluded_chapters || [];

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
      const metadata = deriveEpisodeMetadata(episode, excludedChapters);
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
      SELECT source_id, title, canonical_url
      FROM source_records
      WHERE provider = ? AND source_type = ?
      ORDER BY title
    `)
    .all("Huiji Wiki", "wiki_page");
}

module.exports = {
  DATABASE_PATH,
  REPOSITORY_ROOT,
  formatDuration,
  getCatalogRows,
  getCharacterSourceRows,
  loadMainStoryCatalog,
  openKnowledgeDatabase,
  syncExistingCharacterSources,
  syncMainStoryCatalog,
};

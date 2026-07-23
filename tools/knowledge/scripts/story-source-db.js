const fs = require("node:fs");
const path = require("node:path");
const crypto = require("node:crypto");
const { REPOSITORY_ROOT } = require("./knowledge-db");

const STORY_MANIFEST_PATH = path.join(
  REPOSITORY_ROOT,
  "tools",
  "knowledge",
  "data",
  "huiji_story_text_manifest_v0.1.json"
);
const STORY_INDEX_DIR = path.join(REPOSITORY_ROOT, "indexes", "story_pages");
const STORY_MANUAL_CORRECTIONS_PATH = path.join(
  REPOSITORY_ROOT,
  "tools",
  "knowledge",
  "data",
  "story_manual_corrections_v0.1.json"
);
const STORY_CURATED_MANIFEST_PATH = path.join(
  REPOSITORY_ROOT,
  "tools",
  "knowledge",
  "data",
  "story_curated_manifest_v0.1.json"
);

function stableId(prefix, value) {
  const digest = crypto.createHash("sha1").update(String(value)).digest("hex").slice(0, 12).toUpperCase();
  return `${prefix}-${digest}`;
}

function safeFilename(title) {
  return String(title || "untitled").replace(/[<>:"/\\|?*\u0000-\u001F]/g, "_").trim();
}

function canonicalUrl(title) {
  return `https://f7d.huijiwiki.com/wiki/${encodeURIComponent(title).replace(/%20/g, "_")}`;
}

function relativePath(fullPath) {
  return path.relative(REPOSITORY_ROOT, fullPath).split(path.sep).join("/");
}

function loadStoryManifest() {
  return JSON.parse(fs.readFileSync(STORY_MANIFEST_PATH, "utf8"));
}

function loadStoryManualCorrections() {
  // 人工确认层可在采集链建立前不存在；缺失时按空集合处理，不阻断普通 Wiki 页面入库。
  if (!fs.existsSync(STORY_MANUAL_CORRECTIONS_PATH)) {
    return { claims: [] };
  }

  return JSON.parse(fs.readFileSync(STORY_MANUAL_CORRECTIONS_PATH, "utf8"));
}

function loadStoryCuratedManifest() {
  // 整理层允许按天逐步建立；尚未创建清单时保持空集合，不阻断 raw/clean 正文同步。
  if (!fs.existsSync(STORY_CURATED_MANIFEST_PATH)) {
    return { documents: [] };
  }

  return JSON.parse(fs.readFileSync(STORY_CURATED_MANIFEST_PATH, "utf8"));
}

function readStoryIndex(title) {
  const filePath = path.join(STORY_INDEX_DIR, `${safeFilename(title)}.source.json`);
  if (!fs.existsSync(filePath)) {
    return null;
  }

  return {
    filePath,
    data: JSON.parse(fs.readFileSync(filePath, "utf8")),
  };
}

function ensureStorySchema(database) {
  // story_pages 保留剧情页的范围、路线和正文层路径；它与通用 knowledge_documents 共同构成本地索引。
  database.exec(`
    CREATE TABLE IF NOT EXISTS story_pages (
      story_id TEXT PRIMARY KEY,
      source_id TEXT NOT NULL UNIQUE,
      title TEXT NOT NULL,
      story_scope TEXT NOT NULL,
      route TEXT NOT NULL,
      chapter_label TEXT NOT NULL,
      day_label TEXT NOT NULL,
      collection_status TEXT NOT NULL,
      raw_file_path TEXT,
      clean_file_path TEXT,
      index_file_path TEXT,
      page_id INTEGER,
      touched TEXT,
      section_count INTEGER NOT NULL,
      legacy_video_evidence_json TEXT NOT NULL,
      notes TEXT NOT NULL,
      created_at TEXT NOT NULL,
      updated_at TEXT NOT NULL,
      FOREIGN KEY (source_id) REFERENCES source_records(source_id)
    );

    CREATE TABLE IF NOT EXISTS story_choice_trees (
      choice_tree_id TEXT PRIMARY KEY,
      story_id TEXT NOT NULL,
      source_id TEXT NOT NULL,
      page_title TEXT NOT NULL,
      source_structure TEXT NOT NULL DEFAULT 'unknown',
      branch_type TEXT NOT NULL DEFAULT 'unclassified',
      repeatable INTEGER NOT NULL,
      option_labels_json TEXT NOT NULL,
      exit_option TEXT,
      has_shared_continuation INTEGER NOT NULL,
      extraction_status TEXT NOT NULL,
      created_at TEXT NOT NULL,
      updated_at TEXT NOT NULL,
      FOREIGN KEY (story_id) REFERENCES story_pages(story_id),
      FOREIGN KEY (source_id) REFERENCES source_records(source_id)
    );
  `);

  // SQLite 的旧库已经可能创建过 story_choice_trees；用幂等迁移补齐分支来源与类别字段，
  // 不重建表、不删除既有知识库记录。
  const columns = database.prepare("PRAGMA table_info(story_choice_trees)").all().map((column) => column.name);
  if (!columns.includes("source_structure")) {
    database.exec("ALTER TABLE story_choice_trees ADD COLUMN source_structure TEXT NOT NULL DEFAULT 'unknown';");
  }
  if (!columns.includes("branch_type")) {
    database.exec("ALTER TABLE story_choice_trees ADD COLUMN branch_type TEXT NOT NULL DEFAULT 'unclassified';");
  }
}

function syncStoryManualCorrections(database) {
  const corrections = loadStoryManualCorrections();
  const claims = Array.isArray(corrections.claims) ? corrections.claims : [];
  const timestamp = new Date().toISOString();

  const upsertClaim = database.prepare(`
    INSERT INTO claims (
      claim_id, domain, subject, statement, claim_type, review_status,
      reviewer, reviewed_at, notes, created_at, updated_at
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ON CONFLICT(claim_id) DO UPDATE SET
      domain = excluded.domain,
      subject = excluded.subject,
      statement = excluded.statement,
      claim_type = excluded.claim_type,
      review_status = excluded.review_status,
      reviewer = excluded.reviewer,
      reviewed_at = excluded.reviewed_at,
      notes = excluded.notes,
      updated_at = excluded.updated_at
  `);
  const deleteClaimEvidence = database.prepare("DELETE FROM claim_evidence WHERE claim_id = ?");
  const insertEvidence = database.prepare(`
    INSERT INTO claim_evidence (
      evidence_id, claim_id, source_id, episode_no, source_section,
      start_second, end_second, short_quote, evidence_note, created_at
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
  `);
  const getSource = database.prepare("SELECT source_id FROM source_records WHERE source_id = ?");

  database.exec("BEGIN IMMEDIATE;");
  try {
    for (const claim of claims) {
      const sourceId = stableId("SRC-HUIJI-STORY", claim.page_title || "");
      if (!getSource.get(sourceId)) {
        throw new Error(`人工剧情修正引用了尚未登记的来源页面：${claim.page_title || "未填写页面标题"}`);
      }

      upsertClaim.run(
        claim.claim_id,
        claim.domain || "story_structure",
        claim.subject || "未命名人工剧情修正",
        claim.statement || "",
        claim.claim_type || "narrative_structure",
        claim.review_status || "human_confirmed",
        claim.reviewer || "项目人工确认",
        timestamp,
        claim.evidence_note || "",
        timestamp,
        timestamp
      );

      deleteClaimEvidence.run(claim.claim_id);
      insertEvidence.run(
        stableId("EVIDENCE-STORY", `${claim.claim_id}:${claim.page_title || ""}:${claim.source_section || ""}`),
        claim.claim_id,
        sourceId,
        null,
        claim.source_section || "",
        null,
        null,
        null,
        claim.evidence_note || "",
        timestamp
      );
    }
    database.exec("COMMIT;");
  } catch (error) {
    database.exec("ROLLBACK;");
    throw error;
  }

  return {
    manualCorrectionCount: claims.length,
  };
}

function syncStoryCuratedDocuments(database) {
  const manifest = loadStoryCuratedManifest();
  const documents = Array.isArray(manifest.documents) ? manifest.documents : [];
  const timestamp = new Date().toISOString();
  const getSource = database.prepare("SELECT source_id FROM source_records WHERE source_id = ?");
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
    for (const document of documents) {
      const filePath = String(document.file_path || "").trim();
      const sourcePageTitle = String(document.source_page_title || "").trim();
      if (!filePath || !sourcePageTitle) {
        throw new Error("剧情整理清单缺少 file_path 或 source_page_title。");
      }
      if (!fs.existsSync(path.join(REPOSITORY_ROOT, filePath))) {
        throw new Error(`剧情整理文件不存在：${filePath}`);
      }

      const sourceId = stableId("SRC-HUIJI-STORY", sourcePageTitle);
      if (!getSource.get(sourceId)) {
        throw new Error(`剧情整理引用了尚未登记的来源页面：${sourcePageTitle}`);
      }
      const sourceIndex = readStoryIndex(sourcePageTitle)?.data || {};
      upsertDocument.run(
        document.id || stableId("DOC-STORY-CURATED", filePath),
        "story",
        "curated",
        document.title || path.basename(filePath, ".md"),
        filePath,
        sourceId,
        sourceIndex.last_sync || "",
        document.document_status || "source_structured",
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
    curatedDocumentCount: documents.length,
  };
}

function syncWikiStorySources(database) {
  const manifest = loadStoryManifest();
  const timestamp = new Date().toISOString();
  ensureStorySchema(database);

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
  const upsertStoryPage = database.prepare(`
    INSERT INTO story_pages (
      story_id, source_id, title, story_scope, route, chapter_label, day_label,
      collection_status, raw_file_path, clean_file_path, index_file_path, page_id,
      touched, section_count, legacy_video_evidence_json, notes, created_at, updated_at
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ON CONFLICT(story_id) DO UPDATE SET
      source_id = excluded.source_id,
      title = excluded.title,
      story_scope = excluded.story_scope,
      route = excluded.route,
      chapter_label = excluded.chapter_label,
      day_label = excluded.day_label,
      collection_status = excluded.collection_status,
      raw_file_path = excluded.raw_file_path,
      clean_file_path = excluded.clean_file_path,
      index_file_path = excluded.index_file_path,
      page_id = excluded.page_id,
      touched = excluded.touched,
      section_count = excluded.section_count,
      legacy_video_evidence_json = excluded.legacy_video_evidence_json,
      notes = excluded.notes,
      updated_at = excluded.updated_at
  `);
  const deleteChoiceTrees = database.prepare("DELETE FROM story_choice_trees WHERE source_id = ?");
  const insertChoiceTree = database.prepare(`
    INSERT INTO story_choice_trees (
      choice_tree_id, story_id, source_id, page_title, source_structure, branch_type,
      repeatable, option_labels_json,
      exit_option, has_shared_continuation, extraction_status, created_at, updated_at
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
  `);

  const pages = Array.isArray(manifest.pages) ? manifest.pages : [];
  let collectedCount = 0;
  let missingIndexCount = 0;
  let choiceTreeCount = 0;

  database.exec("BEGIN IMMEDIATE;");
  try {
    for (const entry of pages) {
      const index = readStoryIndex(entry.title);
      const sourceId = stableId("SRC-HUIJI-STORY", entry.title);
      const storyId = entry.id || stableId("STORY", entry.title);
      const sourceIndex = index?.data || {};
      const status = index ? "collected" : entry.status || "seed_for_collection";
      const sourceUrl = sourceIndex.source_url || canonicalUrl(entry.title);
      const lastSync = sourceIndex.last_sync || "";
      const rawPath = sourceIndex.raw_markdown_path || "";
      const cleanPath = sourceIndex.clean_markdown_path || "";
      const indexPath = index ? relativePath(index.filePath) : "";
      const evidence = Array.isArray(entry.legacy_video_evidence)
        ? entry.legacy_video_evidence
        : sourceIndex.legacy_video_evidence || [];

      upsertSource.run(
        sourceId,
        manifest.source_policy?.provider || "Huiji Wiki",
        manifest.source_policy?.source_type || "wiki_page",
        entry.title,
        sourceUrl,
        "",
        "",
        `剧情文本页：${entry.story_scope || "unclassified"} / ${entry.route || "未分类"}`,
        manifest.source_policy?.project_authority || "剧情文本主来源（需人工审核）",
        "保留 raw、clean 与来源索引三层；旧视频记录只作为补充线索。",
        timestamp,
        timestamp
      );

      upsertStoryPage.run(
        storyId,
        sourceId,
        entry.title,
        entry.story_scope || sourceIndex.story_scope || "unclassified",
        entry.route || sourceIndex.route || "",
        entry.chapter || sourceIndex.chapter || "",
        entry.day || sourceIndex.day || "",
        status,
        rawPath,
        cleanPath,
        indexPath,
        Number.isInteger(sourceIndex.page_id) ? sourceIndex.page_id : null,
        sourceIndex.touched || "",
        Array.isArray(sourceIndex.sections) ? sourceIndex.sections.length : 0,
        JSON.stringify(evidence),
        entry.notes || "",
        timestamp,
        timestamp
      );

      // 选择树的正文仍保存在 clean Markdown；此表仅保存可检索的结构索引，不替代原始对白。
      deleteChoiceTrees.run(sourceId);
      for (const [treeIndex, tree] of (sourceIndex.choice_trees || []).entries()) {
        insertChoiceTree.run(
          stableId("STORY-CHOICE", `${storyId}:${treeIndex}:${(tree.options || []).join("|")}`),
          storyId,
          sourceId,
          entry.title,
          tree.source_structure || "unknown",
          tree.branch_type || "unclassified",
          tree.repeatable ? 1 : 0,
          JSON.stringify(tree.options || []),
          tree.exit_option || "",
          tree.has_shared_continuation ? 1 : 0,
          tree.extraction_status || "unclassified",
          timestamp,
          timestamp
        );
        choiceTreeCount += 1;
      }

      if (!index) {
        missingIndexCount += 1;
        continue;
      }

      collectedCount += 1;
      for (const [layer, filePath] of [
        ["raw", rawPath],
        ["clean", cleanPath],
      ]) {
        if (!filePath || !fs.existsSync(path.join(REPOSITORY_ROOT, filePath))) {
          continue;
        }

        upsertDocument.run(
          stableId(`DOC-STORY-${layer.toUpperCase()}`, filePath),
          "story",
          layer,
          entry.title,
          filePath,
          sourceId,
          lastSync,
          "collected",
          timestamp,
          timestamp
        );
      }
    }

    // 视频目录与既有抽样不删除；将其明确降级为补充证据，避免后续摘要误把视频当作正文主来源。
    database.prepare(`
      UPDATE source_records
      SET project_authority = ?, coverage_note = ?, updated_at = ?
      WHERE source_id = ?
    `).run(
      "补充视觉／人工确认来源，不作为剧情正文主来源",
      "保留既有分集目录、时间码与人工记录；Wiki 文本采集完成后，以对应 Wiki 页面为正文依据。",
      timestamp,
      "SRC-BILI-BV17M4Y1W7RR"
    );

    database.exec("COMMIT;");
  } catch (error) {
    database.exec("ROLLBACK;");
    throw error;
  }

  const manualCorrectionResult = syncStoryManualCorrections(database);
  const curatedDocumentResult = syncStoryCuratedDocuments(database);

  return {
    manifestPageCount: pages.length,
    collectedCount,
    missingIndexCount,
    databaseStoryCount: database.prepare("SELECT COUNT(*) AS count FROM story_pages").get().count,
    choiceTreeCount,
    manualCorrectionCount: manualCorrectionResult.manualCorrectionCount,
    curatedDocumentCount: curatedDocumentResult.curatedDocumentCount,
  };
}

function getWikiStoryRows(database) {
  ensureStorySchema(database);
  return database.prepare(`
    SELECT story_pages.title, story_pages.story_scope, story_pages.route, story_pages.chapter_label,
      story_pages.day_label, story_pages.collection_status, story_pages.raw_file_path,
      story_pages.clean_file_path, story_pages.index_file_path, story_pages.section_count,
      (
        SELECT COUNT(*)
        FROM story_choice_trees
        WHERE story_choice_trees.source_id = story_pages.source_id
      ) AS choice_tree_count
    FROM story_pages
    ORDER BY route, day_label DESC, title
  `).all();
}

module.exports = {
  STORY_MANUAL_CORRECTIONS_PATH,
  STORY_CURATED_MANIFEST_PATH,
  STORY_MANIFEST_PATH,
  ensureStorySchema,
  getWikiStoryRows,
  loadStoryCuratedManifest,
  loadStoryManualCorrections,
  loadStoryManifest,
  syncStoryCuratedDocuments,
  syncStoryManualCorrections,
  syncWikiStorySources,
};

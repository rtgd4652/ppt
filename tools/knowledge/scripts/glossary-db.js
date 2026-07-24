const crypto = require("node:crypto");
const fs = require("node:fs");
const path = require("node:path");
const { REPOSITORY_ROOT } = require("./knowledge-db");

const CORE_TERMS_MANIFEST_ID = "core-terms-v0.1";
const CORE_TERMS_MANIFEST_PATH = path.join(
  REPOSITORY_ROOT,
  "tools",
  "knowledge",
  "data",
  "core_terms_v0.1.json"
);
const CORE_TERMS_DOCUMENT_RELATIVE_PATH =
  "knowledge/curated/glossary/core_terms_v0.1.md";
const CORE_TERMS_DOCUMENT_PATH = path.join(
  REPOSITORY_ROOT,
  ...CORE_TERMS_DOCUMENT_RELATIVE_PATH.split("/")
);
const CORE_TERMS_DOCUMENT_ID = "DOC-GLOSSARY-CORE-TERMS-V0.1";

const KNOWLEDGE_LAYERS = new Set([
  "original_fact",
  "project_interpretation",
  "mod_design_decision",
]);
const REVIEW_STATUSES = new Set([
  "pending_source_review",
  "under_review",
  "human_confirmed",
  "needs_special_supplement",
  "project_defined",
  "excluded",
]);
const REFERENCE_TYPES = new Set([
  "wiki_story_page",
  "wiki_character_page",
  "curated_document",
  "project_document",
  "video_supplement",
  "manual_confirmation",
  "external_reference",
]);

function stableReferenceId(termId, reference, referenceNo) {
  const digest = crypto
    .createHash("sha1")
    .update(
      [
        termId,
        reference.reference_type || "",
        reference.source_locator || "",
        reference.source_section || "",
        referenceNo,
      ].join(":")
    )
    .digest("hex")
    .slice(0, 12)
    .toUpperCase();
  return `TERMREF-${digest}`;
}

function loadCoreTermsManifest() {
  if (!fs.existsSync(CORE_TERMS_MANIFEST_PATH)) {
    throw new Error(`核心术语种子不存在：${CORE_TERMS_MANIFEST_PATH}`);
  }
  return JSON.parse(fs.readFileSync(CORE_TERMS_MANIFEST_PATH, "utf8"));
}

function normalizeAlias(alias) {
  if (typeof alias === "string") {
    return {
      alias: alias.trim(),
      alias_type: "alias",
      notes: "",
    };
  }
  return {
    alias: String(alias?.alias || "").trim(),
    alias_type: String(alias?.alias_type || "alias").trim(),
    notes: String(alias?.notes || "").trim(),
  };
}

function normalizeReference(termId, reference, referenceNo) {
  const normalized = {
    reference_id: String(reference?.reference_id || "").trim(),
    reference_type: String(reference?.reference_type || "").trim(),
    source_locator: String(reference?.source_locator || "").trim(),
    source_section: String(reference?.source_section || "").trim(),
    evidence_role: String(reference?.evidence_role || "definition").trim(),
    review_status: String(reference?.review_status || "").trim(),
    notes: String(reference?.notes || "").trim(),
  };
  if (!normalized.reference_id) {
    normalized.reference_id = stableReferenceId(termId, normalized, referenceNo);
  }
  return normalized;
}

function normalizeRelation(relation) {
  return {
    related_term_id: String(relation?.related_term_id || "").trim(),
    relation_type: String(relation?.relation_type || "").trim(),
    notes: String(relation?.notes || "").trim(),
  };
}

function validateCoreTermsManifest(manifest) {
  if (manifest?.schema_version !== "1.0") {
    throw new Error(`不支持的核心术语 schema_version：${manifest?.schema_version || "未填写"}`);
  }
  if (manifest?.manifest_id !== CORE_TERMS_MANIFEST_ID) {
    throw new Error(
      `核心术语 manifest_id 必须为 ${CORE_TERMS_MANIFEST_ID}，实际为 ${manifest?.manifest_id || "未填写"}`
    );
  }
  if (!Array.isArray(manifest.terms) || manifest.terms.length === 0) {
    throw new Error("核心术语种子必须包含至少一个术语。");
  }

  const termIds = new Set();
  const titles = new Map();
  const aliases = new Map();
  const referenceIds = new Set();
  const sortOrders = new Set();
  const normalizedTerms = [];

  for (const [termIndex, term] of manifest.terms.entries()) {
    const termId = String(term?.term_id || "").trim();
    const title = String(term?.title || "").trim();
    const domain = String(term?.domain || "").trim();
    const knowledgeLayer = String(term?.knowledge_layer || "").trim();
    const reviewStatus = String(term?.review_status || "").trim();
    const canonicalSummary = String(term?.canonical_summary || "").trim();
    const usageNote = String(term?.usage_note || "").trim();
    const notes = String(term?.notes || "").trim();
    const suppliedSortOrder = Number(term?.sort_order);
    const sortOrder =
      Number.isInteger(suppliedSortOrder) && suppliedSortOrder > 0
        ? suppliedSortOrder
        : termIndex + 1;

    if (!/^TERM-[A-Z0-9-]+$/.test(termId)) {
      throw new Error(`第 ${termIndex + 1} 个术语的 term_id 无效：${termId || "未填写"}`);
    }
    if (termIds.has(termId)) {
      throw new Error(`核心术语 term_id 重复：${termId}`);
    }
    if (sortOrders.has(sortOrder)) {
      throw new Error(`核心术语 sort_order 重复：${sortOrder}`);
    }
    if (!title || !domain) {
      throw new Error(`${termId} 缺少 title 或 domain。`);
    }
    if (!KNOWLEDGE_LAYERS.has(knowledgeLayer)) {
      throw new Error(`${termId} 的 knowledge_layer 无效：${knowledgeLayer || "未填写"}`);
    }
    if (!REVIEW_STATUSES.has(reviewStatus)) {
      throw new Error(`${termId} 的 review_status 无效：${reviewStatus || "未填写"}`);
    }
    if (reviewStatus === "project_defined" && knowledgeLayer !== "mod_design_decision") {
      throw new Error(`${termId} 标记为 project_defined 时必须属于 mod_design_decision 层。`);
    }
    if (
      ["human_confirmed", "project_defined"].includes(reviewStatus) &&
      !canonicalSummary
    ) {
      throw new Error(`${termId} 已确认或已由项目定义，但 canonical_summary 为空。`);
    }

    const normalizedTitle = title.toLocaleLowerCase("zh-CN");
    if (titles.has(normalizedTitle)) {
      throw new Error(`核心术语标题重复：${title}`);
    }
    titles.set(normalizedTitle, termId);
    termIds.add(termId);
    sortOrders.add(sortOrder);

    const normalizedAliases = (Array.isArray(term.aliases) ? term.aliases : []).map(
      normalizeAlias
    );
    const normalizedReferences = (
      Array.isArray(term.references) ? term.references : []
    ).map((reference, index) =>
      normalizeReference(termId, reference, index + 1)
    );
    const normalizedRelations = (
      Array.isArray(term.relations) ? term.relations : []
    ).map(normalizeRelation);

    if (
      reviewStatus === "human_confirmed" &&
      knowledgeLayer === "original_fact" &&
      normalizedReferences.length === 0
    ) {
      throw new Error(`${termId} 是已确认原作事实，但没有来源引用。`);
    }

    for (const alias of normalizedAliases) {
      if (!alias.alias || !alias.alias_type) {
        throw new Error(`${termId} 含有空别名或空 alias_type。`);
      }
      const normalizedAlias = alias.alias.toLocaleLowerCase("zh-CN");
      if (aliases.has(normalizedAlias)) {
        throw new Error(`核心术语别名重复：${alias.alias}`);
      }
      aliases.set(normalizedAlias, termId);
    }

    for (const reference of normalizedReferences) {
      if (!REFERENCE_TYPES.has(reference.reference_type)) {
        throw new Error(
          `${termId} 的 reference_type 无效：${reference.reference_type || "未填写"}`
        );
      }
      if (!reference.source_locator || !reference.evidence_role) {
        throw new Error(`${termId} 的来源引用缺少 source_locator 或 evidence_role。`);
      }
      if (
        reference.review_status &&
        !REVIEW_STATUSES.has(reference.review_status)
      ) {
        throw new Error(
          `${termId} 的来源引用 review_status 无效：${reference.review_status}`
        );
      }
      if (referenceIds.has(reference.reference_id)) {
        throw new Error(`核心术语 reference_id 重复：${reference.reference_id}`);
      }
      referenceIds.add(reference.reference_id);
    }

    normalizedTerms.push({
      term_id: termId,
      title,
      domain,
      knowledge_layer: knowledgeLayer,
      review_status: reviewStatus,
      canonical_summary: canonicalSummary,
      usage_note: usageNote,
      aliases: normalizedAliases,
      references: normalizedReferences,
      relations: normalizedRelations,
      notes,
      sort_order: sortOrder,
    });
  }

  // 标题和别名在整个清单内必须唯一，防止同一个检索词指向两个概念。
  for (const [normalizedAlias, aliasTermId] of aliases.entries()) {
    const titleTermId = titles.get(normalizedAlias);
    if (titleTermId && titleTermId !== aliasTermId) {
      throw new Error(`术语别名与另一术语标题冲突：${normalizedAlias}`);
    }
  }

  for (const term of normalizedTerms) {
    const relationKeys = new Set();
    for (const relation of term.relations) {
      if (!relation.related_term_id || !relation.relation_type) {
        throw new Error(`${term.term_id} 含有缺少目标或 relation_type 的关系。`);
      }
      if (!termIds.has(relation.related_term_id)) {
        throw new Error(
          `${term.term_id} 的关系引用了清单外术语：${relation.related_term_id}`
        );
      }
      if (relation.related_term_id === term.term_id) {
        throw new Error(`${term.term_id} 不应建立指向自身的术语关系。`);
      }
      const relationKey = `${relation.related_term_id}:${relation.relation_type}`;
      if (relationKeys.has(relationKey)) {
        throw new Error(`${term.term_id} 存在重复术语关系：${relationKey}`);
      }
      relationKeys.add(relationKey);
    }
  }

  return {
    ...manifest,
    terms: normalizedTerms,
  };
}

function normalizeRepositoryPath(sourceLocator) {
  const locatorWithoutAnchor = String(sourceLocator).split("#", 1)[0].trim();
  const normalized = locatorWithoutAnchor.replace(/\\/g, "/");
  if (
    !normalized ||
    normalized.startsWith("/") ||
    /^[A-Za-z]:/.test(normalized) ||
    normalized.split("/").includes("..")
  ) {
    throw new Error(`不安全的仓库相对路径：${sourceLocator}`);
  }

  const fullPath = path.resolve(REPOSITORY_ROOT, ...normalized.split("/"));
  const rootPrefix = `${path.resolve(REPOSITORY_ROOT)}${path.sep}`;
  if (!fullPath.startsWith(rootPrefix)) {
    throw new Error(`来源路径越出仓库：${sourceLocator}`);
  }
  if (!fs.existsSync(fullPath) || !fs.statSync(fullPath).isFile()) {
    throw new Error(`术语引用的本地文件不存在：${normalized}`);
  }
  return {
    relativePath: normalized,
    fullPath,
  };
}

function resolveReference(database, reference) {
  if (reference.reference_type === "wiki_story_page") {
    const story = database
      .prepare("SELECT source_id FROM story_pages WHERE title = ?")
      .get(reference.source_locator);
    if (!story) {
      throw new Error(`术语引用了尚未入库的 Wiki 剧情页：${reference.source_locator}`);
    }
    return {
      sourceLocator: reference.source_locator,
      sourceId: story.source_id,
      documentId: null,
    };
  }

  if (reference.reference_type === "wiki_character_page") {
    const character = database
      .prepare(`
        SELECT source.source_id
        FROM source_records AS source
        INNER JOIN knowledge_documents AS document
          ON document.source_id = source.source_id
        WHERE source.provider = ?
          AND source.source_type = ?
          AND source.title = ?
          AND document.document_type = ?
          AND document.layer = ?
        LIMIT 1
      `)
      .get(
        "Huiji Wiki",
        "wiki_page",
        reference.source_locator,
        "character",
        "clean"
      );
    if (!character) {
      throw new Error(
        `术语引用了尚未入库的 Wiki 角色页：${reference.source_locator}`
      );
    }
    return {
      sourceLocator: reference.source_locator,
      sourceId: character.source_id,
      documentId: null,
    };
  }

  if (
    ["curated_document", "project_document"].includes(reference.reference_type)
  ) {
    const local = normalizeRepositoryPath(reference.source_locator);
    const document = database
      .prepare("SELECT document_id FROM knowledge_documents WHERE file_path = ?")
      .get(local.relativePath);
    return {
      sourceLocator: local.relativePath,
      sourceId: null,
      // 项目设计文档可能尚未进入通用文档索引；路径存在即可保留，
      // 已登记的 curated 文档则同时建立 document_id 关联。
      documentId: document?.document_id || null,
    };
  }

  if (reference.reference_type === "video_supplement") {
    const source = database
      .prepare(`
        SELECT source_id
        FROM source_records
        WHERE source_id = ? OR canonical_url = ? OR title = ?
        LIMIT 1
      `)
      .get(
        reference.source_locator,
        reference.source_locator,
        reference.source_locator
      );
    if (!source) {
      throw new Error(`术语引用了尚未入库的视频来源：${reference.source_locator}`);
    }
    return {
      sourceLocator: reference.source_locator,
      sourceId: source.source_id,
      documentId: null,
    };
  }

  if (
    reference.reference_type === "manual_confirmation" &&
    /[\\/]|\.json(?:#|$)|\.md(?:#|$)/i.test(reference.source_locator)
  ) {
    const local = normalizeRepositoryPath(reference.source_locator);
    return {
      sourceLocator: reference.source_locator.includes("#")
        ? `${local.relativePath}#${reference.source_locator.split("#").slice(1).join("#")}`
        : local.relativePath,
      sourceId: null,
      documentId: null,
    };
  }

  // 纯人工确认标识和外部参考暂不伪造本地来源记录，只保留原始定位。
  return {
    sourceLocator: reference.source_locator,
    sourceId: null,
    documentId: null,
  };
}

function getManagedTermIds(database, manifestId) {
  return database
    .prepare(
      "SELECT term_id FROM glossary_terms WHERE manifest_id = ? ORDER BY sort_order, title"
    )
    .all(manifestId)
    .map((row) => row.term_id);
}

function getCoreTermsDatabaseSummary(database, manifestId = CORE_TERMS_MANIFEST_ID) {
  const termCount = database
    .prepare("SELECT COUNT(*) AS count FROM glossary_terms WHERE manifest_id = ?")
    .get(manifestId).count;
  const aliasCount = database
    .prepare(`
      SELECT COUNT(*) AS count
      FROM glossary_aliases AS alias
      INNER JOIN glossary_terms AS term ON term.term_id = alias.term_id
      WHERE term.manifest_id = ?
    `)
    .get(manifestId).count;
  const referenceCount = database
    .prepare(`
      SELECT COUNT(*) AS count
      FROM glossary_term_references AS reference
      INNER JOIN glossary_terms AS term ON term.term_id = reference.term_id
      WHERE term.manifest_id = ?
    `)
    .get(manifestId).count;
  const relationCount = database
    .prepare(`
      SELECT COUNT(*) AS count
      FROM glossary_relations AS relation
      INNER JOIN glossary_terms AS term ON term.term_id = relation.term_id
      WHERE term.manifest_id = ?
    `)
    .get(manifestId).count;
  const pendingTermCount = database
    .prepare(`
      SELECT COUNT(*) AS count
      FROM glossary_terms
      WHERE manifest_id = ?
        AND review_status IN (
          'pending_source_review',
          'under_review',
          'needs_special_supplement'
        )
    `)
    .get(manifestId).count;
  const document = database
    .prepare(`
      SELECT document_id, document_type, layer, file_path, document_status
      FROM knowledge_documents
      WHERE file_path = ?
    `)
    .get(CORE_TERMS_DOCUMENT_RELATIVE_PATH);

  return {
    manifestId,
    termCount,
    aliasCount,
    referenceCount,
    relationCount,
    pendingTermCount,
    document: document || null,
  };
}

function getCoreTermRows(database, manifestId = CORE_TERMS_MANIFEST_ID) {
  return database
    .prepare(`
      SELECT
        term_id, title, domain, knowledge_layer, review_status,
        canonical_summary, usage_note, manifest_id, sort_order, notes
      FROM glossary_terms
      WHERE manifest_id = ?
      ORDER BY sort_order, title
    `)
    .all(manifestId);
}

function syncCoreTerms(database) {
  const manifest = validateCoreTermsManifest(loadCoreTermsManifest());
  if (
    !fs.existsSync(CORE_TERMS_DOCUMENT_PATH) ||
    !fs.statSync(CORE_TERMS_DOCUMENT_PATH).isFile()
  ) {
    throw new Error(
      `核心术语 Markdown 不存在：${CORE_TERMS_DOCUMENT_RELATIVE_PATH}`
    );
  }

  const timestamp = new Date().toISOString();
  const previousTermIds = getManagedTermIds(database, manifest.manifest_id);
  const currentTermIds = manifest.terms.map((term) => term.term_id);
  const managedTermIds = [...new Set([...previousTermIds, ...currentTermIds])];
  const currentTermIdSet = new Set(currentTermIds);

  const upsertTerm = database.prepare(`
    INSERT INTO glossary_terms (
      term_id, title, domain, knowledge_layer, review_status, canonical_summary,
      usage_note, manifest_id, sort_order, notes, created_at, updated_at
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ON CONFLICT(term_id) DO UPDATE SET
      title = excluded.title,
      domain = excluded.domain,
      knowledge_layer = excluded.knowledge_layer,
      review_status = excluded.review_status,
      canonical_summary = excluded.canonical_summary,
      usage_note = excluded.usage_note,
      manifest_id = excluded.manifest_id,
      sort_order = excluded.sort_order,
      notes = excluded.notes,
      updated_at = excluded.updated_at
  `);
  const insertAlias = database.prepare(`
    INSERT INTO glossary_aliases (term_id, alias, alias_type, notes)
    VALUES (?, ?, ?, ?)
  `);
  const insertReference = database.prepare(`
    INSERT INTO glossary_term_references (
      reference_id, term_id, reference_no, reference_type, source_locator,
      source_id, document_id, source_section, evidence_role, review_status, notes
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
  `);
  const insertRelation = database.prepare(`
    INSERT INTO glossary_relations (
      term_id, related_term_id, relation_type, notes
    ) VALUES (?, ?, ?, ?)
  `);
  const upsertDocument = database.prepare(`
    INSERT INTO knowledge_documents (
      document_id, document_type, layer, title, file_path, source_id,
      last_sync, document_status, indexed_at, updated_at
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ON CONFLICT(file_path) DO UPDATE SET
      document_type = excluded.document_type,
      layer = excluded.layer,
      title = excluded.title,
      source_id = excluded.source_id,
      last_sync = excluded.last_sync,
      document_status = excluded.document_status,
      updated_at = excluded.updated_at
  `);

  database.exec("BEGIN IMMEDIATE;");
  try {
    // 先清理本清单术语拥有的子记录，防止删改别名、证据或关系后留下陈旧索引。
    // 关系只删除本术语发出的记录；其他清单指向本术语的入站关系不属于本清单，
    // 不能在同步时被静默删除。
    for (const termId of managedTermIds) {
      database
        .prepare("DELETE FROM glossary_relations WHERE term_id = ?")
        .run(termId);
      database
        .prepare("DELETE FROM glossary_term_references WHERE term_id = ?")
        .run(termId);
      database.prepare("DELETE FROM glossary_aliases WHERE term_id = ?").run(termId);
    }

    for (const oldTermId of previousTermIds) {
      if (!currentTermIdSet.has(oldTermId)) {
        const inboundRelation = database
          .prepare(`
            SELECT term_id, relation_type
            FROM glossary_relations
            WHERE related_term_id = ?
            LIMIT 1
          `)
          .get(oldTermId);
        if (inboundRelation) {
          throw new Error(
            `不能删除 ${oldTermId}：仍被其他清单术语 ${inboundRelation.term_id} ` +
              `通过 ${inboundRelation.relation_type} 关系引用。`
          );
        }
        database
          .prepare(
            "DELETE FROM glossary_terms WHERE term_id = ? AND manifest_id = ?"
          )
          .run(oldTermId, manifest.manifest_id);
      }
    }

    // 术语必须先全部写入，随后才能建立同一清单内部的外键关系。
    for (const term of manifest.terms) {
      const conflictingTerm = database
        .prepare(
          `SELECT manifest_id
           FROM glossary_terms
           WHERE term_id = ?
             AND manifest_id <> ?
             AND manifest_id <> ''`
        )
        .get(term.term_id, manifest.manifest_id);
      if (conflictingTerm) {
        throw new Error(
          `${term.term_id} 已由其他术语清单管理：${conflictingTerm.manifest_id || "未标记清单"}`
        );
      }
      // 旧数据库中未记录 manifest_id 的同 ID 术语属于 legacy 空归属记录。
      // 当前种子经过完整校验后可安全接管；非空归属仍按上方冲突检查拒绝。
      upsertTerm.run(
        term.term_id,
        term.title,
        term.domain,
        term.knowledge_layer,
        term.review_status,
        term.canonical_summary,
        term.usage_note,
        manifest.manifest_id,
        term.sort_order,
        term.notes,
        timestamp,
        timestamp
      );
    }

    const allTermsReviewed = manifest.terms.every((term) =>
      ["human_confirmed", "project_defined", "excluded"].includes(
        term.review_status
      )
    );
    upsertDocument.run(
      CORE_TERMS_DOCUMENT_ID,
      "glossary",
      "curated",
      "核心术语库 v0.1",
      CORE_TERMS_DOCUMENT_RELATIVE_PATH,
      null,
      "",
      allTermsReviewed ? "reviewed" : "mixed_review",
      timestamp,
      timestamp
    );

    for (const term of manifest.terms) {
      for (const alias of term.aliases) {
        insertAlias.run(term.term_id, alias.alias, alias.alias_type, alias.notes);
      }
      for (const [referenceIndex, reference] of term.references.entries()) {
        const resolved = resolveReference(database, reference);
        insertReference.run(
          reference.reference_id,
          term.term_id,
          referenceIndex + 1,
          reference.reference_type,
          resolved.sourceLocator,
          resolved.sourceId,
          resolved.documentId,
          reference.source_section,
          reference.evidence_role,
          reference.review_status || term.review_status,
          reference.notes
        );
      }
      for (const relation of term.relations) {
        insertRelation.run(
          term.term_id,
          relation.related_term_id,
          relation.relation_type,
          relation.notes
        );
      }
    }

    database.exec("COMMIT;");
  } catch (error) {
    database.exec("ROLLBACK;");
    throw error;
  }

  return getCoreTermsDatabaseSummary(database, manifest.manifest_id);
}

module.exports = {
  CORE_TERMS_DOCUMENT_ID,
  CORE_TERMS_DOCUMENT_PATH,
  CORE_TERMS_DOCUMENT_RELATIVE_PATH,
  CORE_TERMS_MANIFEST_ID,
  CORE_TERMS_MANIFEST_PATH,
  getCoreTermRows,
  getCoreTermsDatabaseSummary,
  loadCoreTermsManifest,
  resolveReference,
  syncCoreTerms,
  validateCoreTermsManifest,
};

const assert = require("node:assert/strict");
const fs = require("node:fs");
const os = require("node:os");
const path = require("node:path");
const test = require("node:test");
const { DatabaseSync } = require("node:sqlite");
const { DATABASE_PATH } = require("../scripts/knowledge-db");
const {
  CORE_TERMS_DOCUMENT_ID,
  CORE_TERMS_DOCUMENT_RELATIVE_PATH,
  CORE_TERMS_MANIFEST_ID,
  extractMarkdownHeadings,
  loadCoreTermsManifest,
  normalizeMarkdownHeading,
  syncCoreTerms,
  validateCoreTermsManifest,
  validateLocalReferenceSection,
} = require("../scripts/glossary-db");

function cloneManifest() {
  return structuredClone(loadCoreTermsManifest());
}

function withTemporaryDatabase(callback) {
  const temporaryDirectory = fs.mkdtempSync(
    path.join(os.tmpdir(), "seven-days-glossary-")
  );
  const temporaryDatabasePath = path.join(
    temporaryDirectory,
    "knowledge-test.sqlite"
  );
  fs.copyFileSync(DATABASE_PATH, temporaryDatabasePath);
  const database = new DatabaseSync(temporaryDatabasePath);
  database.exec("PRAGMA foreign_keys = ON;");

  try {
    return callback(database);
  } finally {
    database.close();
    fs.rmSync(temporaryDirectory, { recursive: true, force: true });
  }
}

function getCoreSnapshot(database) {
  return {
    terms: database
      .prepare(`
        SELECT
          term_id, title, domain, knowledge_layer, review_status,
          canonical_summary, usage_note, manifest_id, sort_order, notes
        FROM glossary_terms
        WHERE manifest_id = ?
        ORDER BY term_id
      `)
      .all(CORE_TERMS_MANIFEST_ID),
    aliases: database
      .prepare(`
        SELECT alias.term_id, alias.alias, alias.alias_type, alias.notes
        FROM glossary_aliases AS alias
        INNER JOIN glossary_terms AS term ON term.term_id = alias.term_id
        WHERE term.manifest_id = ?
        ORDER BY alias.term_id, alias.alias
      `)
      .all(CORE_TERMS_MANIFEST_ID),
    references: database
      .prepare(`
        SELECT
          reference.reference_id, reference.term_id, reference.reference_no,
          reference.reference_type, reference.source_locator,
          reference.source_id, reference.document_id, reference.source_section,
          reference.evidence_role, reference.review_status, reference.notes
        FROM glossary_term_references AS reference
        INNER JOIN glossary_terms AS term ON term.term_id = reference.term_id
        WHERE term.manifest_id = ?
        ORDER BY reference.term_id, reference.reference_no
      `)
      .all(CORE_TERMS_MANIFEST_ID),
    relations: database
      .prepare(`
        SELECT
          relation.term_id, relation.related_term_id,
          relation.relation_type, relation.notes
        FROM glossary_relations AS relation
        INNER JOIN glossary_terms AS term ON term.term_id = relation.term_id
        WHERE term.manifest_id = ?
        ORDER BY relation.term_id, relation.related_term_id, relation.relation_type
      `)
      .all(CORE_TERMS_MANIFEST_ID),
    document: database
      .prepare(`
        SELECT
          document_id, document_type, layer, title, file_path,
          source_id, last_sync, document_status
        FROM knowledge_documents
        WHERE file_path = ?
      `)
      .get(CORE_TERMS_DOCUMENT_RELATIVE_PATH),
  };
}

function insertExternalTerm(database, termId, title) {
  const timestamp = "2026-01-01T00:00:00.000Z";
  database
    .prepare(`
      INSERT INTO glossary_terms (
        term_id, title, domain, knowledge_layer, review_status,
        canonical_summary, usage_note, manifest_id, sort_order, notes,
        created_at, updated_at
      ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    `)
    .run(
      termId,
      title,
      "测试",
      "project_interpretation",
      "under_review",
      "仅用于临时数据库回归测试。",
      "",
      "test-external-manifest",
      1,
      "",
      timestamp,
      timestamp
    );
}

test("Manifest 严格拒绝非数组字段与无效排序", () => {
  assert.doesNotThrow(() => validateCoreTermsManifest(cloneManifest()));

  for (const field of ["aliases", "references", "relations"]) {
    for (const invalidValue of [undefined, null, {}, ""]) {
      const manifest = cloneManifest();
      manifest.terms[0][field] = invalidValue;
      assert.throws(
        () => validateCoreTermsManifest(manifest),
        new RegExp(`${field} 必须是数组`)
      );
    }
  }

  for (const invalidSortOrder of [undefined, null, "1", 0, -1, 1.5]) {
    const manifest = cloneManifest();
    manifest.terms[0].sort_order = invalidSortOrder;
    assert.throws(
      () => validateCoreTermsManifest(manifest),
      /sort_order 必须是正整数/
    );
  }
});

test("Manifest 使用 NFKC 检测标题与别名冲突", () => {
  const manifest = cloneManifest();
  manifest.terms[0].title = "ＡＢＣ";
  manifest.terms[1].aliases.push({
    alias: " ABC ",
    alias_type: "alias",
    notes: "临时测试别名。",
  });
  assert.throws(
    () => validateCoreTermsManifest(manifest),
    /术语别名与术语标题冲突/
  );
});

test("Markdown 章节提取忽略代码围栏中的伪标题", () => {
  const headings = extractMarkdownHeadings(
    "# 真实标题\n\n```text\n# 代码示例\n```\n\n   ## 第二节\n"
  );
  assert.deepEqual(headings, ["# 真实标题", "   ## 第二节"]);
  assert.equal(normalizeMarkdownHeading("7日轮回"), "7日轮回");
  assert.equal(normalizeMarkdownHeading("7. 轮回结构"), "轮回结构");
});

test("本地文档引用必须填写并唯一匹配真实章节", () => {
  const temporaryDirectory = fs.mkdtempSync(
    path.join(os.tmpdir(), "seven-days-heading-")
  );
  const markdownPath = path.join(temporaryDirectory, "heading-test.md");
  fs.writeFileSync(markdownPath, "# 第一节\n\n## 第二节（补充说明）\n", "utf8");
  const local = {
    relativePath: "heading-test.md",
    fullPath: markdownPath,
  };

  try {
    assert.doesNotThrow(() =>
      validateLocalReferenceSection(
        { source_section: "第二节" },
        local
      )
    );
    assert.throws(
      () => validateLocalReferenceSection({ source_section: "" }, local),
      /source_section 不得为空/
    );
    assert.throws(
      () =>
        validateLocalReferenceSection(
          { source_section: "不存在的章节" },
          local
        ),
      /不存在章节/
    );
  } finally {
    fs.rmSync(temporaryDirectory, { recursive: true, force: true });
  }
});

test("核心术语连续同步保持幂等", { concurrency: false }, () => {
  withTemporaryDatabase((database) => {
    syncCoreTerms(database);
    const firstSnapshot = getCoreSnapshot(database);
    syncCoreTerms(database);
    const secondSnapshot = getCoreSnapshot(database);
    assert.deepEqual(secondSnapshot, firstSnapshot);
  });
});

test("身份一致的 legacy 记录可接管，身份不一致时拒绝并回滚", () => {
  const firstTerm = validateCoreTermsManifest(cloneManifest()).terms[0];

  withTemporaryDatabase((database) => {
    database
      .prepare("UPDATE glossary_terms SET manifest_id = '' WHERE term_id = ?")
      .run(firstTerm.term_id);
    assert.doesNotThrow(() => syncCoreTerms(database));
    const adopted = database
      .prepare("SELECT manifest_id FROM glossary_terms WHERE term_id = ?")
      .get(firstTerm.term_id);
    assert.equal(adopted.manifest_id, CORE_TERMS_MANIFEST_ID);
  });

  withTemporaryDatabase((database) => {
    database
      .prepare(`
        UPDATE glossary_terms
        SET manifest_id = '', title = ?
        WHERE term_id = ?
      `)
      .run("错误的旧记录", firstTerm.term_id);
    const before = database
      .prepare(`
        SELECT title, manifest_id
        FROM glossary_terms
        WHERE term_id = ?
      `)
      .get(firstTerm.term_id);
    assert.throws(() => syncCoreTerms(database), /拒绝自动接管/);
    const after = database
      .prepare(`
        SELECT title, manifest_id
        FROM glossary_terms
        WHERE term_id = ?
      `)
      .get(firstTerm.term_id);
    assert.deepEqual(after, before);
  });
});

test("跨清单标题和别名冲突会在写入前拒绝", () => {
  const manifest = validateCoreTermsManifest(cloneManifest());
  const firstTitle = manifest.terms[0].title;
  const firstAlias = manifest.terms.find((term) => term.aliases.length > 0)
    .aliases[0].alias;

  withTemporaryDatabase((database) => {
    insertExternalTerm(database, "TERM-TEST-EXTERNAL-TITLE", firstTitle);
    const before = getCoreSnapshot(database);
    assert.throws(() => syncCoreTerms(database), /冲突/);
    assert.deepEqual(getCoreSnapshot(database), before);
  });

  withTemporaryDatabase((database) => {
    insertExternalTerm(database, "TERM-TEST-EXTERNAL-ALIAS", "外部测试术语");
    database
      .prepare(`
        INSERT INTO glossary_aliases (term_id, alias, alias_type, notes)
        VALUES (?, ?, ?, ?)
      `)
      .run(
        "TERM-TEST-EXTERNAL-ALIAS",
        firstTitle,
        "alias",
        "临时测试别名。"
      );
    const before = getCoreSnapshot(database);
    assert.throws(() => syncCoreTerms(database), /冲突/);
    assert.deepEqual(getCoreSnapshot(database), before);
  });

  withTemporaryDatabase((database) => {
    insertExternalTerm(
      database,
      "TERM-TEST-EXTERNAL-CURRENT-ALIAS",
      firstAlias
    );
    const before = getCoreSnapshot(database);
    assert.throws(() => syncCoreTerms(database), /冲突/);
    assert.deepEqual(getCoreSnapshot(database), before);
  });
});

test("同步保留其他清单指向核心术语的入站关系", () => {
  withTemporaryDatabase((database) => {
    insertExternalTerm(database, "TERM-TEST-EXTERNAL-INBOUND", "外部入站测试");
    const targetTermId = validateCoreTermsManifest(cloneManifest()).terms[0]
      .term_id;
    database
      .prepare(`
        INSERT INTO glossary_relations (
          term_id, related_term_id, relation_type, notes
        ) VALUES (?, ?, ?, ?)
      `)
      .run(
        "TERM-TEST-EXTERNAL-INBOUND",
        targetTermId,
        "references",
        "临时回归测试。"
      );

    syncCoreTerms(database);
    const relation = database
      .prepare(`
        SELECT notes
        FROM glossary_relations
        WHERE term_id = ?
          AND related_term_id = ?
          AND relation_type = ?
      `)
      .get("TERM-TEST-EXTERNAL-INBOUND", targetTermId, "references");
    assert.equal(relation.notes, "临时回归测试。");
  });
});

test("核心术语文档 ID 与路径冲突时拒绝同步", () => {
  withTemporaryDatabase((database) => {
    database.exec("PRAGMA foreign_keys = OFF;");
    database
      .prepare(`
        UPDATE knowledge_documents
        SET document_id = ?
        WHERE document_id = ?
      `)
      .run("DOC-TEST-WRONG-GLOSSARY-ID", CORE_TERMS_DOCUMENT_ID);
    database.exec("PRAGMA foreign_keys = ON;");

    assert.throws(() => syncCoreTerms(database), /核心术语文档路径已由/);
  });
});

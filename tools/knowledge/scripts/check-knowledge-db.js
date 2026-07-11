const fs = require("node:fs");
const path = require("node:path");
const {
  DATABASE_PATH,
  REPOSITORY_ROOT,
  getCatalogRows,
  getCharacterSourceRows,
  loadMainStoryCatalog,
  openKnowledgeDatabase,
} = require("./knowledge-db");

const REQUIRED_OUTPUTS = [
  path.join(REPOSITORY_ROOT, "knowledge", "curated", "sources", "bilibili_main_story_BV17M4y1w7rr.md"),
  path.join(REPOSITORY_ROOT, "knowledge", "curated", "sources", "huiji_character_source_index_v0.1.md"),
  path.join(REPOSITORY_ROOT, "knowledge", "curated", "videos", "main_story_catalog_v0.1.md"),
  path.join(REPOSITORY_ROOT, "knowledge", "curated", "reviews", "main_story_core_01_03_review_queue_v0.1.md"),
];

function fail(message) {
  console.error(`检查失败：${message}`);
  process.exitCode = 1;
}

if (!fs.existsSync(DATABASE_PATH)) {
  fail("本地 SQLite 数据库尚未初始化。请先运行 init-knowledge-db.js。");
} else {
  const catalog = loadMainStoryCatalog();
  const database = openKnowledgeDatabase();

  try {
    const source = database.prepare("SELECT source_id FROM source_records WHERE source_id = ?").get(catalog.source.id);
    const rows = getCatalogRows(database, catalog.source.id);
    const characterSources = getCharacterSourceRows(database);
    const excluded = rows.filter((row) => row.editorial_status === "excluded");
    const priority = rows.filter((row) => row.priority_batch === "core_chapters_01_03");

    if (!source) {
      fail(`缺少来源记录：${catalog.source.id}`);
    }
    if (rows.length !== 85) {
      fail(`目录分集数量应为 85，实际为 ${rows.length}。`);
    }
    if (excluded.length !== 2 || excluded.some((row) => row.chapter_number !== 12)) {
      fail("第 12 章排除规则不正确。");
    }
    if (priority.length !== 12) {
      fail(`前三章首批队列应为 12 集，实际为 ${priority.length}。`);
    }
    if (characterSources.length !== 7) {
      fail(`灰机角色来源应为 7 条，实际为 ${characterSources.length}。`);
    }
    for (const outputPath of REQUIRED_OUTPUTS) {
      if (!fs.existsSync(outputPath)) {
        fail(`缺少导出文档：${outputPath}`);
      }
    }

    if (!process.exitCode) {
      console.log("本地知识库数据库检查通过。");
      console.log(`来源记录：${source.source_id}`);
      console.log(`分集目录：${rows.length}`);
      console.log(`排除分集：${excluded.length}`);
      console.log(`首批队列：${priority.length}`);
      console.log(`灰机角色来源：${characterSources.length}`);
    }
  } finally {
    database.close();
  }
}

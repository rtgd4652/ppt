const { openKnowledgeDatabase } = require("./knowledge-db");
const { syncCoreTerms } = require("./glossary-db");

// 独立同步入口：只把已提交的核心术语种子与 Markdown 索引写入 SQLite，
// 不联网、不改写术语文档，也不重复采集剧情或角色页面。
const database = openKnowledgeDatabase();

try {
  const result = syncCoreTerms(database);
  console.log("核心术语已同步到本地知识库数据库。");
  console.log(`术语：${result.termCount}`);
  console.log(`别名：${result.aliasCount}`);
  console.log(`来源引用：${result.referenceCount}`);
  console.log(`术语关系：${result.relationCount}`);
  console.log(`待审核术语：${result.pendingTermCount}`);
} finally {
  database.close();
}

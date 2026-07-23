const { openKnowledgeDatabase } = require("./knowledge-db");
const { syncWikiStorySources } = require("./story-source-db");

// 独立同步入口：剧情采集器只写文件，本脚本负责把已经验证的页面写入本地 SQLite。
const database = openKnowledgeDatabase();

try {
  const result = syncWikiStorySources(database);
  console.log("Wiki 剧情文本已同步到本地知识库数据库。");
  console.log(`清单页面：${result.manifestPageCount}`);
  console.log(`已采集页面：${result.collectedCount}`);
  console.log(`待采集页面：${result.missingIndexCount}`);
  console.log(`数据库剧情页：${result.databaseStoryCount}`);
  console.log(`已识别选择树：${result.choiceTreeCount}`);
  console.log(`人工剧情修正：${result.manualCorrectionCount}`);
  console.log(`已登记剧情整理：${result.curatedDocumentCount}`);
} finally {
  database.close();
}

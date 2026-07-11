const {
  DATABASE_PATH,
  openKnowledgeDatabase,
  syncExistingCharacterSources,
  syncMainStoryCatalog,
} = require("./knowledge-db");

// 初始化或更新本地 SQLite 索引；目录种子数据始终来自已提交的 JSON 文件。
const database = openKnowledgeDatabase();

try {
  const result = syncMainStoryCatalog(database);
  const characterResult = syncExistingCharacterSources(database);
  console.log("本地知识库数据库已初始化。");
  console.log(`数据库：${DATABASE_PATH}`);
  console.log(`主线目录：${result.episodeCount} 集`);
  console.log(`总时长：${Math.floor(result.totalDurationSeconds / 3600)} 小时 ${Math.floor((result.totalDurationSeconds % 3600) / 60)} 分钟`);
  console.log(`编辑排除：${result.excludedCount} 集`);
  console.log(`前三章首批队列：${result.priorityCount} 集`);
  console.log(`灰机角色来源：${characterResult.characterSourceCount} 条`);
  console.log(`Clean 角色文档：${characterResult.cleanCharacterCount} 条`);
} finally {
  database.close();
}

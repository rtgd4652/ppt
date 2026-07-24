const {
  DATABASE_PATH,
  openKnowledgeDatabase,
  syncExistingCharacterSources,
  syncMainStoryRouteComparison,
  syncManualStoryReviews,
  syncMainStoryCatalog,
} = require("./knowledge-db");
const { syncWikiStorySources } = require("./story-source-db");
const { syncCoreTerms } = require("./glossary-db");

// 初始化或更新本地 SQLite 索引；目录种子数据始终来自已提交的 JSON 文件。
const database = openKnowledgeDatabase();

try {
  const result = syncMainStoryCatalog(database);
  const manualReviewResult = syncManualStoryReviews(database);
  const routeComparisonResult = syncMainStoryRouteComparison(database);
  const characterResult = syncExistingCharacterSources(database);
  const storyResult = syncWikiStorySources(database);
  // 术语来源可能引用剧情页和 curated 文档，因此必须放在剧情同步之后。
  const glossaryResult = syncCoreTerms(database);
  console.log("本地知识库数据库已初始化。");
  console.log(`数据库：${DATABASE_PATH}`);
  console.log(`主线目录：${result.episodeCount} 集`);
  console.log(`总时长：${Math.floor(result.totalDurationSeconds / 3600)} 小时 ${Math.floor((result.totalDurationSeconds % 3600) / 60)} 分钟`);
  console.log(`编辑排除：${result.excludedCount} 集`);
  console.log(`前三章首批队列：${result.priorityCount} 集`);
  console.log(`人工审核记录：${manualReviewResult.reviewCount} 条`);
  console.log(`人工摘要时间段：${manualReviewResult.segmentCount} 条`);
  console.log(`路线对照记录：${routeComparisonResult.comparisonCount} 条`);
  console.log(`路线对照项：${routeComparisonResult.entryCount} 项`);
  console.log(`灰机角色来源：${characterResult.characterSourceCount} 条`);
  console.log(`Clean 角色文档：${characterResult.cleanCharacterCount} 条`);
  console.log(`Wiki 剧情清单：${storyResult.manifestPageCount} 页`);
  console.log(`Wiki 已采集剧情：${storyResult.collectedCount} 页`);
  console.log(`核心术语：${glossaryResult.termCount} 条`);
  console.log(`术语来源引用：${glossaryResult.referenceCount} 条`);
  console.log(`待审核术语：${glossaryResult.pendingTermCount} 条`);
} finally {
  database.close();
}

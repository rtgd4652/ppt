# 本地 SQLite 数据库

数据库文件 `seven_days_knowledge.sqlite` 由 `tools/knowledge/scripts/init-knowledge-db.js` 创建。

它保存来源、视频分集目录、术语、事实、证据和审核记录的结构化索引。数据库二进制文件不提交到 Git；可由已提交的目录种子数据与工具脚本重新生成。

当前种子内容：

- B 站主线剧情合集 `BV17M4y1w7rr` 的 85 集目录。
- 七名现有角色的灰机 Wiki 来源与 clean 文档索引。
- 第 12 章《堕天使的挽歌》的排除规则。
- 主线第 1 至 3 章的首批人工摘要队列。

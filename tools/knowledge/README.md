# 本地知识库工具

本目录维护《神器使》Stellaris Mod 的本地结构化知识库。它不修改 `mod/`，不下载视频，也不自动把社区资料视为原作事实。

## 存储原则

- `raw/`：原始采集资料，便于回溯。
- `knowledge/characters/`：可重新生成的 clean 资料。
- `knowledge/mod_ready/`：Stellaris 转化候选，不等同于原作事实。
- `knowledge/curated/`：人工审核后的来源、术语、事实与审核页面。
- `knowledge/database/seven_days_knowledge.sqlite`：本地 SQLite 结构化索引；由工具与已提交种子数据重建，不提交二进制文件。

## 常用命令

在仓库根目录运行：

```powershell
node tools/knowledge/scripts/init-knowledge-db.js
node tools/knowledge/scripts/export-main-story-catalog.js
node tools/knowledge/scripts/check-knowledge-db.js
```

## 当前主线视频规则

- 目录来源为 B 站主线剧情合集 `BV17M4y1w7rr`。
- 该来源经项目人工确认，可作为 Wiki 缺失主线剧情时的主要叙事证据。
- 每一条正式剧情事实仍须记录分集编号、时间码、原创摘要与人工审核结果。
- 第 12 章《堕天使的挽歌》按项目编辑决定排除。
- 不下载视频、不保存视频帧、不复制长篇台词；当前阶段不安装或使用自动转写工具。

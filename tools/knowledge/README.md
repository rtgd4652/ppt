# 本地知识库工具

本目录维护《神器使》Stellaris Mod 的本地结构化知识库。它不修改 `mod/`，不下载视频，也不自动把社区资料视为原作事实。

## 存储原则

- `raw/`：原始采集资料，便于回溯。
- `knowledge/characters/`：可重新生成的 clean 资料。
- `knowledge/mod_ready/`：Stellaris 转化候选，不等同于原作事实。
- `knowledge/curated/`：人工审核后的来源、术语、事实与审核页面。
- `knowledge/database/seven_days_knowledge.sqlite`：本地 SQLite 结构化索引；由工具与已提交种子数据重建，不提交二进制文件。
- `knowledge/story/pages/`：灰机 Wiki 剧情页的 clean 正文层；每页都对应 `raw/huiji/stories/` 与 `indexes/story_pages/`。
- `knowledge/story/curated/days/`：按单日逐步建立的结构化剧情整理层；每份文件必须在 `tools/knowledge/data/story_curated_manifest_v0.1.json` 中登记后再同步入库。
- `story_choice_trees`：SQLite 中保存已验证的剧情选择树结构索引；记录来源结构、分支类别、可重复标记、选项、结束选项与识别状态，正文仍以 clean Markdown 为准。

## 常用命令

在仓库根目录运行：

```powershell
node tools/knowledge/scripts/init-knowledge-db.js
node tools/knowledge/scripts/export-main-story-catalog.js
node tools/knowledge/scripts/check-knowledge-db.js
node tools/knowledge/scripts/sync-wiki-story-sources.js
node tools/knowledge/scripts/check-wiki-story-text.js
```

长视频人工审核需要临时画面抽样时，可传入页面地址和一个或多个秒数：

```powershell
node tools/knowledge/scripts/review-bilibili-memory.js "https://www.bilibili.com/video/BV17M4y1w7rr/?p=9" 150 300 450
```

该脚本只在内存中定位并返回画面，不保存截图、不下载视频，也不读取字幕。

## 当前剧情来源规则

- 灰机 Wiki 的公开剧情文本是当前项目的剧情正文主来源。
- 先逐页保存 raw、clean、来源索引三件套，再基于可追溯文本编写人工审核摘要。
- 不进行全站自动同步；剧情页必须先进入 `tools/knowledge/data/huiji_story_text_manifest_v0.1.json`，再逐页采集。
- 已有 B 站目录、时间码与抽样记录不删除，但降级为补充视觉／人工确认线索，不能覆盖 Wiki 文本。

## 既有主线视频记录

- 目录来源为 B 站主线剧情合集 `BV17M4y1w7rr`。
- 该来源保留为 Wiki 缺失或需要人工视觉核对时的补充证据。
- 每一条正式剧情事实仍须记录分集编号、时间码、原创摘要与人工审核结果。
- P01 是 07:00 的新手引导剧情，仅保留为游戏进入时的上下文，不作为主线剧情 1 的完整叙事证据。
- P02 起的主线剧情 1 属于游戏背景剧情，不归入角色个人主线；审核时优先记录世界背景、城市处境、主线冲突与分歧节点。
- P08《彩蛋——闪闪发光的迷之钥》经项目人工确认排除。
- 第 12 章《堕天使的挽歌》按项目编辑决定排除。
- 不下载视频、不保存视频帧、不复制长篇台词；当前阶段不安装或使用自动转写工具。

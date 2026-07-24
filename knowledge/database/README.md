# 本地 SQLite 数据库

数据库文件 `seven_days_knowledge.sqlite` 由 `tools/knowledge/scripts/init-knowledge-db.js` 创建。

它保存来源、视频分集目录、术语、事实、证据和审核记录的结构化索引。数据库二进制文件不提交到 Git；可由已提交的目录种子数据与工具脚本重新生成。

当前种子内容：

- B 站主线剧情合集 `BV17M4y1w7rr` 的 85 集目录。
- 八名现有角色的灰机 Wiki 来源与 clean 文档索引，其中包含主线剧情 2 的核心角色“安”。
- P01 新手引导的范围确认，以及 P02 游戏背景主线 `00:00–01:13:14` 的全片首轮分段审核记录；其中 30:00–36:00、42:00–48:00、54:00–60:00 已获人工确认。
- P03（结局 1“箱庭风景”）`00:00–12:00` 的独立首轮审核记录；跨结局结论暂不生成。
- P08《彩蛋——闪闪发光的迷之钥》与第 12 章《堕天使的挽歌》的排除规则。
- 主线第 1 至 3 章（排除 P08）的首批人工摘要队列。
- `tools/knowledge/data/core_terms_v0.1.json` 中登记的核心术语、别名、来源引用与术语关系。

## 核心术语表

- `glossary_terms`：规范术语、知识层级、审核状态与简明定义。
- `glossary_aliases`：术语别名，不允许同一检索词指向多个概念。
- `glossary_term_references`：术语的 Wiki 页面、本地文档、视频补充或人工确认定位。
- `glossary_relations`：同一清单内术语之间的结构关系。

核心术语由 `manifest_id = core-terms-v0.1` 管理。同步器仅清理和更新该清单所属记录，
不删除其他术语，也不修改 `story_pages`、`story_choice_trees`、`claims` 等既有知识表。
旧库中同 ID 且尚无清单归属的术语可由当前清单接管；已归属其他清单的同 ID 记录会被拒绝。
其他清单指向核心术语的入站关系不会被同步器删除；若删除术语会破坏此类关系，同步会回滚。

初始化数据库：

```powershell
node tools/knowledge/scripts/init-knowledge-db.js
```

只同步核心术语：

```powershell
node tools/knowledge/scripts/sync-core-terms.js
```

完整检查：

```powershell
node tools/knowledge/scripts/check-knowledge-db.js
```

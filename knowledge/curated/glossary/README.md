# 核心术语库

本目录保存《神器使》Stellaris Mod 的核心术语规范，用于统一知识库、设计文档、本地化、剧情文案与后续脚本中的概念用法。

## 权威文件

- `core_terms_v0.1.md`：供开发者阅读、审核和引用的人类可读版。
- `../../../tools/knowledge/data/core_terms_v0.1.json`：供校验器和本地数据库同步使用的机器可读唯一种子。
- `core_terms_review_queue_v0.1.md`：早期来源重建队列，只保留为历史审核记录，不再作为正式定义来源。

SQLite 数据库只是检索索引，不是术语定义的编辑入口。不要直接修改数据库中的术语记录。

## 三层知识边界

1. `original_fact`：原作资料直接支持的事实或原作术语。
2. `project_interpretation`：项目根据多份来源做出的结构化整理，不冒充原作原句。
3. `mod_design_decision`：为本 Mod 世界观延伸或功能系统作出的设计决定。

任何 Mod 设计决定都不得反向改写为原作事实。任何角色推测都不得直接提升为宇宙真理。

## 审核状态

- `human_confirmed`：已完成人工校订。
- `under_review`：已有来源，但定义边界仍需继续核验。
- `pending_source_review`：需要补充直接来源或身份核验。
- `project_defined`：由项目明确作出的设计决定。

## 维护流程

1. 先在来源页、角色资料或项目圣经中补充证据。
2. 修改 `tools/knowledge/data/core_terms_v0.1.json`。
3. 同步更新 `core_terms_v0.1.md`。
4. 运行：

   ```powershell
   node tools/knowledge/scripts/sync-core-terms.js
   node tools/knowledge/scripts/check-knowledge-db.js
   ```

5. 检查术语别名是否与其他规范词或别名冲突。
6. 检查术语关系目标、来源路径和审核状态是否有效。

新增术语时，必须同时说明“是什么”“不是什么”“适用范围”和“证据层级”。

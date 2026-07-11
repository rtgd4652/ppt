# 项目架构索引

本目录定义 v0.2 及以后版本的长期开发架构。它负责说明模块边界、稳定标识、迁移顺序和 Git 工作流，不直接定义玩法数值。

## 架构目标

1. 保持 `mod/` 是唯一游戏运行目录。
2. 让白夜馆、角色、文明经济、成长路线、舰船和巨构能够独立维护。
3. 新角色不再继续堆入以爱缪莎命名的公共文件。
4. 保持 v0.1 存档可识别的事件 ID、对象 key、flag 和 event target 稳定。
5. 每次只迁移一个模块，并用静态检查和游戏内复测验证。

## 文档

- `runtime_architecture_v0.2.md`：运行目录、模块依赖与目标文件布局。
- `naming_and_compatibility.md`：命名、编码、公共 ID 与存档兼容规则。
- `migration_plan_v0.2.md`：从当前结构迁移到目标结构的阶段计划。
- `branch_release_workflow.md`：分支、提交、测试、合并与标签规则。
- `../../reports/v0.2_architecture_baseline_report.md`：本轮盘点、验证结果与运行内容隔离记录。

## 五层结构

```text
raw / indexes
    ↓
knowledge
    ↓
docs / design
    ↓
mod
    ↓
tools / validation → reports → release
```

- `raw/` 与 `indexes/` 保存可追溯的外部资料和索引。
- `knowledge/` 保存清洗后的事实、世界观圣经和角色档案。
- `docs/` 保存开发决策、玩法设计、架构和版本管理文档。
- `mod/` 只保存 Stellaris 实际加载内容。
- `tools/` 和 `reports/` 分别保存自动化工具与验证结果。

## 当前约束

- `parallel/v1-integration` 是 v0.1.0 封版候选，不再接受架构重排。
- 架构准备在 `refactor/v0.2-architecture` 上进行。
- 在 v0.1.0 正式标签创建前，不拆分或重命名现有运行对象。
- 缺失图标等待统一美术规范，不进入本轮架构工作。

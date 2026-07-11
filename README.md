# SevenDays_Mod

《永远的七日之都》主题 Stellaris Mod 项目仓库。

当前候选版本：`0.1.0`。游戏内复测通过后发布 `v0.1.0` 标签。

v0.2 架构准备在独立分支 `refactor/v0.2-architecture` 进行，不改变 v0.1 候选版的运行内容。

## 仓库结构

```text
SevenDays_Mod/
├── mod/             # 真正给 Stellaris 加载的模组目录
├── knowledge/       # 七日之都世界观、角色、组织、时间线知识库
├── assets/          # 开发期素材，不直接作为最终 Mod 根目录加载
├── docs/            # 路线图、设计文档、TODO、变更记录
├── tools/           # 爬虫、解析、导出、构建辅助工具
└── README.md
```

## 本地加载方式

Stellaris 启动器应该指向 `mod/` 目录，而不是仓库根目录。

当前实际模组目录：

```text
C:\Users\Admin\Desktop\ppt\simple_leader_edict\mod
```

`mod/descriptor.mod` 是真正给游戏读取的描述文件。仓库根目录只负责管理源码、素材、文档和工具。

## 开发约定

- `mod/` 内只放游戏运行需要读取的内容。
- `assets/official_reference/` 只放参考资料，不作为最终 Mod 内容发布。
- AI 图、Blender 源文件、概念图放入 `assets/ai_generated/` 或对应素材目录。
- 生成脚本、转换脚本、导出脚本放入 `tools/`。
- 所有 Stellaris 脚本继续添加中文注释。
- 不覆盖原版文件，尽量保持纯新增。

## 当前核心内容

- 神器使物种、特质、起源、预设帝国。
- 白夜馆招募、联络、档案展示与管理入口。
- 爱缪莎、赛斯、幽桐、拉比四名可招募领袖。
- 领袖唯一招募、职业、专属特质、等级成长与立绘切换基础。
- 专属传统、飞升、科技、建筑、区划、岗位。
- 命运之主舰船、专属核心组件、双光环、跃迁核心、重构事件与模型。
- 命运观测塔巨构与后续建模规划。

## 当前封版边界

- 白夜馆不是世界观组织或政治势力。
- v0.1 暂不实装安托涅瓦、晏华和格蕾莎。
- 命运之主因模型尚无正式武器 locator，暂时关闭武器槽。
- 缺失图标等待统一美术规范后集中制作。

项目进度与测试入口：

- `docs/PROJECT_STATUS.md`
- `docs/project/v0.1_release_freeze.md`
- `reports/v0.1_manual_test_checklist.md`

## 架构与验证入口

- 架构总览：`docs/architecture/README.md`
- 运行时模块边界：`docs/architecture/runtime_architecture_v0.2.md`
- 命名与兼容规则：`docs/architecture/naming_and_compatibility.md`
- v0.2 渐进迁移顺序：`docs/architecture/migration_plan_v0.2.md`
- 分支与发布流程：`docs/architecture/branch_release_workflow.md`
- 静态验证工具：`tools/build/validation/README.md`
- 架构基线报告：`reports/v0.2_architecture_baseline_report.md`

默认静态验证不会把暂缓制作的正式图标视为阻断错误：

```powershell
node tools/build/validation/validate-mod.js
```

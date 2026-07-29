# 1.0 神器使角色状态档案索引

本目录记录十名锁定神器使从资料、设计、美术、实现到测试的当前状态。它是项目管理层，不替代原作 clean 资料、Mod Ready 摘要、标准角色档案或游戏脚本。

逐项完成关卡、资料阻塞与当前执行顺序见：

- [1.0 十名神器使完成矩阵](../v1.0_character_completion_matrix.md)

## 状态字段

| 字段 | 可用状态 | 含义 |
| --- | --- | --- |
| 名单状态 | `locked` | 已进入 1.0 不可替换基线 |
| 原作资料 | `complete` / `partial` / `missing` | clean 与来源链是否足以支撑设计 |
| Mod Ready | `complete` / `partial` / `missing` | 是否已有结构化转化摘要 |
| 标准角色档案 | `complete` / `partial` / `missing` | 是否已按统一模板完成角色档案 |
| 游戏实现 | `playable` / `partial` / `not_started` | 是否已能在游戏内完整招募与使用 |
| 美术锚点 | `approved` / `partial` / `deferred` / `missing` | 原作视觉依据与制作边界状态 |
| 叙事设计 | `approved` / `partial` / `blocked` | 角色在 1.0 中的叙事职责是否确定 |
| 测试状态 | `passed` / `partial` / `not_tested` | 1.0 角色专项测试状态 |

`complete` 和 `approved` 只对对应字段生效。例如“标准角色档案 complete”不代表游戏实现或美术已经完成。

## 十人索引

- [安托涅瓦](antoniva_status_v1.0.md)
- [爱缪莎](aemusa_status_v1.0.md)
- [晏华](yanhua_status_v1.0.md)
- [安](an_status_v1.0.md)
- [赛斯](seth_status_v1.0.md)
- [幽桐](yutong_status_v1.0.md)
- [拉比](rabi_status_v1.0.md)
- [格蕾莎](greysa_status_v1.0.md)
- [雯梓](wenzi_status_v1.0.md)
- [里见茜](satomi_akane_status_v1.0.md)

## 更新纪律

1. 只记录已验证的当前状态，不用“预计完成”冒充“已完成”。
2. 每次状态变化必须注明验证依据或文件路径。
3. 发现原作事实冲突时，回到来源与人工校订层解决；不要直接在状态档案中选择答案。
4. 游戏实现完成后仍需通过唯一招募、职业、特质、立绘、本地化、读档与 `error.log` 测试，才能将测试状态改为 `passed`。
5. 1.0 名单由 [`ED-009`](../../curated/decisions/project_editorial_decisions_v0.1.md) 锁定，状态档案无权自行增删角色。

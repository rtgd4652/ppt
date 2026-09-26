---
title: "爱缪莎 1.0 主线状态命名方案"
type: "state_naming_design"
version: "1.0-approved"
status: "approved_state_naming_baseline"
implementation_authorized: false
last_updated: "2026-08-16"
---

# 爱缪莎 1.0 主线状态命名方案

## 0. 定位

本文为未来 Stellaris 代码预留一致、可搜索、可审计的状态命名体系。所有名称目前都是候选名，不是已存在的脚本定义；批准本文也不会自动授权创建它们。

## 1. 总前缀

爱缪莎 1.0 主线统一使用：

```text
aemusa_ms_
```

其中：

- `aemusa`：角色与项目域；
- `ms`：main story，主线专用；
- 后续部分按所有者、类别、对象和状态排列。

禁止在新主线状态中混用：

- `artifact_`；
- `destiny_lord_`；
- `aemusa_fp_`；
- 无域前缀的通用词；
- 旧舰船和旧巨构名称。

现有旧 key 继续作为历史实现保留，只有专项迁移批准后才处理，不在本方案中批量改名。

## 2. 基本格式

```text
aemusa_ms_<owner>_<category>_<object>_<state>
```

| 段 | 示例 | 含义 |
| --- | --- | --- |
| `owner` | `country`、`leader`、`crisis`、`truth`、`decision` | 语义所有者，不一定直接等于脚本 scope |
| `category` | `chapter`、`cluster`、`loss`、`route`、`gate` | 状态类别 |
| `object` | `ch14`、`aed_14_30`、`vanilla_crisis` | 被记录对象 |
| `state` | `started`、`completed`、`settled`、`paused` | 明确状态 |

名称只使用小写 ASCII、数字和下划线。不要使用中文、空格、连字符、角色显示名或未经批准的资产名。

## 3. 状态类型后缀

| 技术类型 | 命名后缀 | 用途 |
| --- | --- | --- |
| country flag | 直接使用完整状态名 | 布尔事实、永久结算、互斥选择 |
| leader flag | `_leader_flag` 仅在确需领袖对象持有时使用 | 临时或角色自身表现，不作为路线唯一事实 |
| variable | `_value`、`_index`、`_count` | 枚举索引、计数和可比较数值 |
| saved target | `_target` | 可替换对象定位，不单独证明历史完成 |
| global flag | `_global` | 仅真正跨国家、跨对象的全局事实 |
| temporary flag | `_temp` | 窗口和表现状态，禁止作为权威账本 |

不要仅凭名字推断技术类型；未来状态登记表必须另列 scope、数据类型和生命周期。

## 4. 事件簇四阶段命名

以 `AED-14-30` 为例：

```text
aemusa_ms_country_cluster_aed_14_30_started
aemusa_ms_country_cluster_aed_14_30_in_progress
aemusa_ms_country_cluster_aed_14_30_completed
aemusa_ms_country_cluster_aed_14_30_settled
```

约束：

1. `started` 表示通过入口并开始，不等于完成；
2. `in_progress` 用于需要跨日、跨项目或跨窗口恢复的阶段；
3. `completed` 表示叙事和选择完成，尚未执行唯一结算；
4. `settled` 表示所有不可逆写入已经完成；
5. 同一事件簇不得同时处于两个活动阶段；
6. 已 `settled` 后不再回到前三种状态。

若简单叙事簇不需要跨日，可以在同一次合法流程中依次写入，但四阶段语义仍须在测试证据中可区分。

## 5. 章节与幕命名

```text
aemusa_ms_country_chapter_00_completed
aemusa_ms_country_chapter_01_completed
...
aemusa_ms_country_chapter_16_completed
aemusa_ms_country_epilogue_completed
```

幕完成使用：

```text
aemusa_ms_country_act_01_completed
...
aemusa_ms_country_act_06_completed
```

章节入口必须通过上一章结算和相应外部历史，不允许只看 `chapter_XX_completed` 单一条件。

## 6. 七组账本候选域

| 账本 | 候选前缀 | 示例 |
| --- | --- | --- |
| 历史进度 | `aemusa_ms_country_history_` | `aemusa_ms_country_history_fallen_empire_war_completed` |
| 文明选择 | `aemusa_ms_country_civilization_` | `aemusa_ms_country_civilization_information_policy_recorded` |
| 关系与责任 | `aemusa_ms_country_responsibility_` | `aemusa_ms_country_responsibility_review_completed` |
| 损失账本 | `aemusa_ms_country_loss_` | `aemusa_ms_country_loss_ledger_locked` |
| 真相层级 | `aemusa_ms_truth_` | `aemusa_ms_truth_world_difference_mutually_confirmed` |
| 终局资格 | `aemusa_ms_country_final_gate_` | `aemusa_ms_country_final_gate_level_30_met` |
| 双方决定 | `aemusa_ms_decision_` | `aemusa_ms_decision_player_authorized` |

示例只说明结构，不批准具体实现数量。

## 7. 原版危机互斥命名

候选危机身份使用单一枚举变量：

```text
aemusa_ms_country_vanilla_crisis_route_index
```

建议枚举值：

| 值 | 含义 |
| --- | --- |
| `0` | 尚未选择 |
| `1` | 候选模块一 |
| `2` | 候选模块二 |
| `3` | 候选模块三 |
| `4` | 候选模块四 |

具体候选与数值映射必须在实现登记表中写明，不能依赖开发者记忆。

同时只保留通用里程碑：

```text
aemusa_ms_country_history_vanilla_crisis_locked
aemusa_ms_country_history_vanilla_crisis_started
aemusa_ms_country_history_vanilla_crisis_completed
aemusa_ms_country_history_vanilla_crisis_settled
```

不要为每种候选建立可以并存的四套“completed”布尔标记，避免多路线同时成立。

## 8. 专属危机命名域

专属危机统一使用：

```text
aemusa_ms_crisis_
```

类别包括：

- `phase_`：危机阶段；
- `anchor_`：终局锚点生命周期；
- `projection_`：无人格投影；
- `loss_`：危机永久损失；
- `weakness_`：弱点资料；
- `megastructure_`：巨构职责状态；
- `local_stabilization_`：现场局部恒定职责。

禁止出现：

- `enemy_leader`、`crisis_ruler` 等人格领袖语义；
- 未批准正式舰名或巨构名；
- `destiny_lord`、`fate_observatory` 等旧案绑定；
- 把“命运规律”写成国家或角色所有者的命名。

## 9. 真相层级命名

候选命名：

```text
aemusa_ms_truth_civilization_facts_settled
aemusa_ms_truth_fate_is_impersonal_confirmed
aemusa_ms_truth_world_difference_mutually_confirmed
aemusa_ms_truth_player_continuity_mutually_confirmed
aemusa_ms_truth_central_court_visibility_index
aemusa_ms_truth_aemusa_visibility_index
aemusa_ms_truth_open_mysteries_locked
```

角色知情应使用独立索引或明确事实，不使用一个全局 `truth_known`。

任何高层真相必须同时检查：

- 内容事实是否已经成立；
- 当前读取主体是否拥有对应可见等级；
- 展示媒介是否属于公开、角色或私人场景。

## 10. 六种双方决定命名

建议用一个权威枚举变量表示总体状态，并用两个独立永久事实证明双方决定来源。

### 10.1 总体枚举

```text
aemusa_ms_decision_joint_state_index
```

| 值 | 状态 |
| --- | --- |
| `0` | 未决定 |
| `1` | 暂缓 |
| `2` | 玩家拒绝 |
| `3` | 授权待回应 |
| `4` | 爱缪莎拒绝 |
| `5` | 双方同意 |

### 10.2 来源事实

```text
aemusa_ms_decision_player_authorized
aemusa_ms_decision_player_refused
aemusa_ms_decision_aemusa_accepted
aemusa_ms_decision_aemusa_refused
```

互斥约束：

- 玩家授权与玩家拒绝不能并存；
- 爱缪莎接受与爱缪莎拒绝不能并存；
- 总体状态 `5` 必须同时拥有玩家授权和爱缪莎接受；
- 总体状态 `2` 必须拥有玩家拒绝且没有玩家授权；
- 总体状态 `4` 必须拥有玩家授权和爱缪莎拒绝；
- 状态 `1` 不产生任何永久决定来源事实。

总体枚举不能单独证明双方真实决定；来源事实也不能绕过总体状态审计直接进入第十六章。

## 11. 终局资格与权限命名

候选资格：

```text
aemusa_ms_country_final_gate_level_30_met
aemusa_ms_country_final_gate_history_complete
aemusa_ms_country_final_gate_crises_complete
aemusa_ms_country_final_gate_truth_complete
aemusa_ms_country_final_gate_responsibility_complete
aemusa_ms_country_final_gate_all_met
```

候选终局事实：

```text
aemusa_ms_country_ending_non_transform_player_refusal_settled
aemusa_ms_country_ending_non_transform_aemusa_refusal_settled
aemusa_ms_country_ending_fate_sovereign_settled
aemusa_ms_country_fate_sovereign_authority_active
aemusa_ms_country_epilogue_tone_index
aemusa_ms_country_story_v1_complete
```

`fate_sovereign_authority_active` 只能由第十六章唯一结算产生。它不能从等级、危机胜利、身份文本或美术资源存在推导。

## 12. 暂停与恢复原因命名

使用一个可枚举的暂停原因和必要的补充事实：

```text
aemusa_ms_country_pause_reason_index
aemusa_ms_country_pause_active
```

暂停原因至少区分：

- 玩家主动暂缓；
- 等级资格不足；
- 责任／制度修复不足；
- 资料复盘不足；
- 角色暂时不可用；
- 表现性中断；
- 状态冲突硬阻断。

硬阻断不是普通暂停，必须另有：

```text
aemusa_ms_country_consistency_conflict_active
aemusa_ms_country_consistency_conflict_index
```

不能通过清除 `pause_active` 来解决状态冲突。

## 13. 唯一结算命名

一次性结算统一使用：

```text
aemusa_ms_country_settlement_<object>_done
```

例如：

```text
aemusa_ms_country_settlement_aed_16_10_done
aemusa_ms_country_settlement_vanilla_crisis_done
aemusa_ms_country_settlement_exclusive_crisis_done
aemusa_ms_country_settlement_epilogue_done
```

任何一次性奖励或解锁还应有自己的结果事实，结算保护与结果事实不能共用一个含糊标记。

## 14. 临时对象和保存目标

候选保存目标：

```text
aemusa_ms_aemusa_leader_target
aemusa_ms_current_scene_target
aemusa_ms_current_anchor_target
aemusa_ms_megastructure_target
```

规则：

1. 爱缪莎领袖对象可重新定位，但路线历史不能只存在领袖对象上；
2. 场景和锚点目标缺失时，根据权威账本恢复或硬阻断，不能重建永久结果；
3. 巨构被占领时所有权可以变化，已验证资料仍保存在路线／文明账本；
4. temporary target 不得证明章节完成、玩家决定或结局成立。

## 15. 本地化与日志命名

本地化候选前缀：

```text
aemusa_ms_event_
aemusa_ms_option_
aemusa_ms_tooltip_
aemusa_ms_block_reason_
aemusa_ms_audit_
```

日志和调试输出必须包含：

- 事件簇规划编号；
- 当前状态所有者；
- 旧状态与目标状态；
- 阻断或结算原因；
- 是否属于测试注入。

新增脚本中的中文注释应解释“为什么需要该状态”和“何时不可重复”，不能只翻译 key 名。

## 16. 状态登记表要求

代码阶段开始前必须另建机器可审查的状态登记表，每一项至少包含：

- 正式 key；
- 中文说明；
- 所有者和 Stellaris scope；
- 数据类型；
- 默认值；
- 合法写入接口；
- 合法读取接口；
- 生命周期；
- 互斥和前置；
- 唯一结算要求；
- 迁移／调试边界；
- 对应 AED 规划编号和测试编号。

没有登记的状态不得在实现阶段临时加入主线。

## 17. ASN-R001 审核记录

请审核：

1. 是否批准主线统一使用 `aemusa_ms_` 前缀，并与旧舰船、旧巨构和现有不一致 key 隔离；
2. 是否批准 `owner + category + object + state` 的基本格式及事件簇四阶段命名；
3. 是否批准七组账本候选域、原版天灾单一枚举和专属危机独立命名域；
4. 是否批准真相层级不使用单一 `truth_known`，而按事实、角色可见等级和展示媒介分别检查；
5. 是否批准六种双方决定使用总体枚举加四个独立来源事实，并执行明确互斥规则；
6. 是否批准终局资格、非转变结局、命运主宰权限和尾声分别命名，禁止从等级或危机胜利推导权限；
7. 是否批准暂停、硬冲突、唯一结算与临时保存目标各自使用独立命名语义；
8. 是否确认正式 key 仍需状态登记表和另行代码授权，本文件不触碰旧 key。

审核结果：2026-08-16 用户明确批准。`aemusa_ms_` 主线前缀、所有者／类别／对象／状态结构、事件簇四阶段、七组账本命名域、原版天灾单一枚举、专属危机隔离域、真相分层、六种双方决定总体枚举与独立来源事实、终局资格、暂停、冲突、唯一结算和临时对象命名规则正式锁定。

本文自此成为爱缪莎 1.0 主线候选状态命名基线。`implementation_authorized` 继续保持 `false`：正式 key 仍须进入状态登记表并获得代码授权，现有旧 key 不在本次审核中修改。

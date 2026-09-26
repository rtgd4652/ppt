---
title: "爱缪莎 1.0 主线状态登记表"
type: "state_registry_design"
version: "1.0-approved"
status: "approved_state_registry_baseline"
implementation_authorized: false
awp_00_implementation_authorized: true
awp_00_status: "completed_runtime_pass"
awp_01_implementation_authorized: true
awp_01_status: "completed_runtime_pass"
last_updated: "2026-08-16"
---

# 爱缪莎 1.0 主线状态登记表

## 0. 文档职责

本文登记未来实现可以使用的候选权威状态。它受以下已批准文档约束：

1. [`aemusa_main_story_event_decomposition_v1.0.md`](aemusa_main_story_event_decomposition_v1.0.md)；
2. [`aemusa_main_story_implementation_interface_v1.0.md`](aemusa_main_story_implementation_interface_v1.0.md)；
3. [`aemusa_main_story_state_naming_v1.0.md`](aemusa_main_story_state_naming_v1.0.md)。

登记状态不等于创建脚本。本文获批后，正式 key 仍须在代码授权阶段逐项落地；未经登记的主线状态不得在实现中临时添加。

## 1. 登记字段

| 字段 | 含义 |
| --- | --- |
| 登记号 | 文档中的稳定引用编号 |
| 候选 key | 未来脚本候选名称 |
| 语义所有者 | 七组权威账本或外部模块 |
| 建议 scope | 未来可能使用的 Stellaris 作用域 |
| 类型 | flag、variable、saved target 或 pattern |
| 默认值 | 新开局初始状态 |
| 合法写入接口 | 唯一允许改变该状态的接口职责 |
| 生命周期 | 临时、章节、路线永久或存档永久 |
| 互斥／前置 | 必须同时满足的约束 |
| 对应规划 | AED 事件簇或跨章规则 |
| 测试 | 最小覆盖测试编号 |

建议 scope 只是设计输入；代码阶段必须对照 Stellaris 4.4.3 真实作用域重新验证。

## 2. 路线骨架与事件簇状态

| 登记号 | 候选 key | 所有者 | scope | 类型 | 默认值 | 合法写入接口 | 生命周期 | 互斥／前置 | 对应规划 | 测试 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ASR-001 | `aemusa_ms_country_route_initialized` | 历史进度 | country | flag | no | 路线初始化唯一结算 | 存档永久 | 玩家国家与爱缪莎路线资格成立 | 全线 | T001/T003 |
| ASR-002 | `aemusa_ms_country_route_version_index` | 历史进度 | country | variable | 0 | 路线初始化／批准的迁移接口 | 存档永久 | 只能单调升级 | 全线 | T004/T017 |
| ASR-003 | `aemusa_ms_country_chapter_index` | 历史进度 | country | variable | 0 | 章节唯一结算 | 存档永久 | 只能推进到已结算章节 | 全线 | T001/T002 |
| ASR-004 | `aemusa_ms_country_act_index` | 历史进度 | country | variable | 0 | 幕唯一结算 | 存档永久 | 对应章节全部结算 | 全线 | T001/T002 |
| ASR-005 | `aemusa_ms_country_story_v1_complete` | 历史进度 | country | flag | no | 成功或非转变结局结算 | 存档永久 | 必须存在一种合法终局结果 | NT／AED-16 | T012/T013/T016 |
| ASR-006 | `aemusa_ms_country_cluster_<aed_id>_started` | 历史进度 | country | pattern flag | no | `begin_story_cluster` | 事件簇永久 | 入口检查通过 | 所有 AED 簇 | T001-T004 |
| ASR-007 | `aemusa_ms_country_cluster_<aed_id>_in_progress` | 历史进度 | country | pattern flag | no | 事件簇操作接口 | 事件簇 | 已 started、未 completed | 所有跨窗口 AED 簇 | T004 |
| ASR-008 | `aemusa_ms_country_cluster_<aed_id>_completed` | 历史进度 | country | pattern flag | no | `complete_story_cluster` | 事件簇永久 | 子步骤完成、未 settled | 所有 AED 簇 | T003/T004 |
| ASR-009 | `aemusa_ms_country_cluster_<aed_id>_settled` | 历史进度 | country | pattern flag | no | `settle_story_cluster_once` | 存档永久 | completed 且唯一结算未执行 | 所有 AED 簇 | T003/T016 |
| ASR-010 | `aemusa_ms_country_chapter_<chapter_id>_completed` | 历史进度 | country | pattern flag | no | 章节唯一结算 | 存档永久 | 本章必需 AED 簇均 settled | PRO、01-16、EPI | T001/T002 |
| ASR-011 | `aemusa_ms_country_act_<act_id>_completed` | 历史进度 | country | pattern flag | no | 幕唯一结算 | 存档永久 | 本幕必需章节完成 | ACT 01-06 | T001/T002 |

`<aed_id>` 使用规划编号的 ASCII 形式，例如 `aed_14_30`。模式行在代码阶段必须展开为经审核的显式 key 清单，不允许脚本运行时拼接 key。

## 3. 战争与危机历史

| 登记号 | 候选 key | 所有者 | scope | 类型 | 默认值 | 合法写入接口 | 生命周期 | 互斥／前置 | 对应规划 | 测试 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ASR-020 | `aemusa_ms_country_history_fallen_empire_war_started` | 历史进度 | country | flag | no | 失落帝国战争适配器 | 存档永久 | 第四章结算 | AED-05-00 | T001/T002 |
| ASR-021 | `aemusa_ms_country_history_fallen_empire_war_completed` | 历史进度 | country | flag | no | 战争结果适配器 | 存档永久 | 战争真实结束 | AED-06-00 | T002/T004 |
| ASR-022 | `aemusa_ms_country_history_fallen_empire_war_settled` | 历史进度 | country | flag | no | 第六章唯一结算 | 存档永久 | 战后复盘完成 | AED-06-90 | T002/T003 |
| ASR-023 | `aemusa_ms_country_vanilla_crisis_route_index` | 历史进度 | country | variable | 0 | 原版危机路线锁定接口 | 存档永久 | 只能从 0 变为 1-4 一次 | AED-C-00 | T005/T017 |
| ASR-024 | `aemusa_ms_country_history_vanilla_crisis_locked` | 历史进度 | country | flag | no | 原版危机路线锁定接口 | 存档永久 | route_index 为 1-4 | AED-C-00 | T005 |
| ASR-025 | `aemusa_ms_country_history_vanilla_crisis_started` | 历史进度 | country | flag | no | 原版危机事实适配器 | 存档永久 | 候选已锁定且危机真实开始 | AED-C-10 | T005 |
| ASR-026 | `aemusa_ms_country_history_vanilla_crisis_completed` | 历史进度 | country | flag | no | 原版危机结果适配器 | 存档永久 | 已锁定候选真实完成 | AED-C-50 | T005 |
| ASR-027 | `aemusa_ms_country_history_vanilla_crisis_settled` | 历史进度 | country | flag | no | 第七章入口唯一结算 | 存档永久 | 完成事实与贡献复盘有效 | AED-C-50 | T005/T006 |
| ASR-028 | `aemusa_ms_crisis_exclusive_initialized` | 专属危机 | country | flag | no | 专属危机初始化接口 | 存档永久 | 第十章完成、每局仅一次 | AED-11-00 | T006 |
| ASR-029 | `aemusa_ms_crisis_exclusive_phase_index` | 专属危机 | country | variable | 0 | 专属危机状态机 | 危机至路线永久 | 单调推进，不倒退 | AED-11 至 AED-13 | T006/T017 |
| ASR-030 | `aemusa_ms_crisis_exclusive_completed` | 专属危机 | country | flag | no | 专属危机双钥匙结算 | 存档永久 | 毁灭载体清除且未来重开 | AED-13-20 | T006/T008 |
| ASR-031 | `aemusa_ms_crisis_exclusive_settled` | 历史进度 | country | flag | no | 危机唯一胜利结算 | 存档永久 | completed 且未失败 | AED-13-30 | T006/T016 |
| ASR-032 | `aemusa_ms_crisis_exclusive_irreversible_failure` | 历史进度 | country | flag | no | 专属危机失败唯一结算 | 存档永久 | 与 completed／settled 互斥 | AED-11 至 AED-13 | T017 |

## 4. 文明选择、关系与责任

| 登记号 | 候选 key | 所有者 | scope | 类型 | 默认值 | 合法写入接口 | 生命周期 | 互斥／前置 | 对应规划 | 测试 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ASR-040 | `aemusa_ms_country_civilization_action_tempo_index` | 文明选择 | country | variable | 0 | 已批准行动节奏选择结算 | 存档永久 | 只能记录已展示选择 | 跨章 | T018 |
| ASR-041 | `aemusa_ms_country_civilization_information_policy_index` | 文明选择 | country | variable | 0 | 信息治理选择结算 | 存档永久 | 公开范围可追溯 | 跨章 | T018/T019 |
| ASR-042 | `aemusa_ms_country_civilization_responsibility_radius_index` | 文明选择 | country | variable | 0 | 责任半径选择结算 | 存档永久 | 不等于善恶值 | AED-01／02 | T018 |
| ASR-043 | `aemusa_ms_country_civilization_diplomacy_recorded` | 文明选择 | country | flag | no | 外交行动复盘 | 存档永久 | 必须来自现实行动 | 跨章 | T018 |
| ASR-044 | `aemusa_ms_country_civilization_rescue_recorded` | 文明选择 | country | flag | no | 救援行动复盘 | 存档永久 | 必须来自现实行动 | 跨章 | T008/T018 |
| ASR-045 | `aemusa_ms_country_civilization_reality_contribution_recorded` | 文明选择 | country | flag | no | 危机贡献适配器 | 存档永久 | 不由文本伪造 | 原版／专属危机 | T005/T006 |
| ASR-046 | `aemusa_ms_country_responsibility_ledger_initialized` | 关系与责任 | country | flag | no | 序章责任账本初始化 | 存档永久 | 路线已初始化 | PRO | T001 |
| ASR-047 | `aemusa_ms_country_responsibility_disagreement_recorded` | 关系与责任 | country | flag | no | 对应选择结算 | 存档永久 | 不因修复删除 | 跨章 | T004/T018 |
| ASR-048 | `aemusa_ms_country_responsibility_sacrifice_recorded` | 关系与责任 | country | flag | no | 损失／选择结算 | 存档永久 | 不因胜利删除 | 跨章 | T008/T018 |
| ASR-049 | `aemusa_ms_country_responsibility_repair_required` | 关系与责任 | country | flag | no | 责任审计接口 | 可恢复至完成 | 有真实缺口 | AED-08 至 AED-15 | T010/T011 |
| ASR-050 | `aemusa_ms_country_responsibility_repair_completed` | 关系与责任 | country | flag | no | 责任恢复接口 | 存档永久 | required 且真实修复完成 | AED-10／14／15 | T010/T011 |
| ASR-051 | `aemusa_ms_country_responsibility_final_review_completed` | 关系与责任 | country | flag | no | 最终资格审计 | 存档永久 | 历史、裂痕和修复均已读取 | AED-15-00 | T010/T015 |

## 5. 损失与专属危机资料

| 登记号 | 候选 key | 所有者 | scope | 类型 | 默认值 | 合法写入接口 | 生命周期 | 互斥／前置 | 对应规划 | 测试 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ASR-060 | `aemusa_ms_country_loss_ledger_initialized` | 损失账本 | country | flag | no | 首次现实损失结算 | 存档永久 | 路线已初始化 | 跨章 | T008 |
| ASR-061 | `aemusa_ms_country_loss_has_permanent_losses` | 损失账本 | country | flag | no | 永久损失接口 | 存档永久 | 至少一项真实永久损失 | 跨章 | T008 |
| ASR-062 | `aemusa_ms_country_loss_ledger_locked_for_ending` | 损失账本 | country | flag | no | 第十三章代价清点 | 存档永久 | 专属危机已结算 | AED-13-40 | T008/T016 |
| ASR-063 | `aemusa_ms_crisis_anchor_result_ledger_locked` | 专属危机 | country | flag | no | 多锚点结果汇总 | 存档永久 | 所有活动锚点已有终态 | AED-12-60／13 | T006/T008 |
| ASR-064 | `aemusa_ms_crisis_weakness_verified` | 专属危机 | country | flag | no | 巨构弱点验证接口 | 存档永久 | 真实资料达到验证标准 | AED-12-40 | T007 |
| ASR-065 | `aemusa_ms_crisis_weakness_published` | 文明选择 | country | flag | no | 资料公开结算 | 存档永久 | verified 且玩家批准公开 | AED-12-40 | T007/T019 |
| ASR-066 | `aemusa_ms_crisis_megastructure_analysis_paused` | 专属危机 | country | flag | no | 巨构占领适配器 | 占领期间 | 巨构被占领 | AED-12-40 | T007 |
| ASR-067 | `aemusa_ms_crisis_local_stabilization_available` | 专属危机 | country | flag | no | 局部恒定职责适配器 | 危机期间 | 不绑定具体载体 | AED-12-10／13-20 | T006/T020 |

## 6. 真相层级

| 登记号 | 候选 key | 所有者 | scope | 类型 | 默认值 | 合法写入接口 | 生命周期 | 互斥／前置 | 对应规划 | 测试 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ASR-070 | `aemusa_ms_truth_civilization_facts_settled` | 真相层级 | country | flag | no | 文明证据复盘结算 | 存档永久 | 专属危机已结算 | AED-14-10 | T009/T019 |
| ASR-071 | `aemusa_ms_truth_fate_is_impersonal_confirmed` | 真相层级 | country | flag | no | 命运去人格化结算 | 存档永久 | 文明证据充分 | AED-14-10 | T009/T019 |
| ASR-072 | `aemusa_ms_truth_boundary_layers_locked` | 真相层级 | country | flag | no | 四层矩阵审计 | 存档永久 | 埃索林证言边界有效 | AED-14-20 | T009/T019 |
| ASR-073 | `aemusa_ms_truth_world_difference_mutually_confirmed` | 终局互认 | country | flag | no | 爱缪莎／玩家互认结算 | 存档永久 | 专属危机后、四层矩阵完成 | AED-14-30 | T009 |
| ASR-074 | `aemusa_ms_truth_player_continuity_mutually_confirmed` | 终局互认 | country | flag | no | 爱缪莎／玩家互认结算 | 存档永久 | 与 world_difference 同场确认 | AED-14-30 | T009 |
| ASR-075 | `aemusa_ms_truth_central_court_visibility_index` | 角色知情 | country | variable | 0 | 真相层级服务 | 存档永久 | 只能按证据升级 | 跨章 | T009/T019 |
| ASR-076 | `aemusa_ms_truth_aemusa_visibility_index` | 角色知情 | country | variable | 0 | 真相层级服务 | 存档永久 | 危机前不能达到终局互认层 | 跨章 | T009/T019 |
| ASR-077 | `aemusa_ms_truth_open_mysteries_locked` | 开放谜团 | country | flag | no | 谜团登记结算 | 存档永久 | 只能登记未知，不能回答 | AED-14-20／EPI | T019 |

## 7. 终局资格与双方决定

| 登记号 | 候选 key | 所有者 | scope | 类型 | 默认值 | 合法写入接口 | 生命周期 | 互斥／前置 | 对应规划 | 测试 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ASR-080 | `aemusa_ms_country_final_gate_level_30_met` | 终局资格 | country | flag | no | 最终资格审计 | 可重检后永久 | 爱缪莎真实达到 30 级 | AED-14／15 | T010 |
| ASR-081 | `aemusa_ms_country_final_gate_history_complete` | 终局资格 | country | flag | no | 最终资格审计 | 存档永久 | 必需章节和战争历史完整 | AED-15-00 | T010/T015 |
| ASR-082 | `aemusa_ms_country_final_gate_crises_complete` | 终局资格 | country | flag | no | 最终资格审计 | 存档永久 | 原版与专属危机均已结算 | AED-15-00 | T010/T015 |
| ASR-083 | `aemusa_ms_country_final_gate_truth_complete` | 终局资格 | country | flag | no | 最终资格审计 | 存档永久 | AED-14-30 已结算 | AED-15-00 | T009/T015 |
| ASR-084 | `aemusa_ms_country_final_gate_responsibility_complete` | 终局资格 | country | flag | no | 最终资格审计 | 存档永久 | 责任终审完成 | AED-15-00 | T010/T015 |
| ASR-085 | `aemusa_ms_country_final_gate_all_met` | 终局资格 | country | flag | no | 最终资格汇总审计 | 可重检后永久 | ASR-080 至 084 全部成立 | AED-15-00 | T010/T015 |
| ASR-086 | `aemusa_ms_decision_joint_state_index` | 双方决定 | country | variable | 0 | 双方决定服务 | 存档永久 | 值 0-5，合法状态单向转移 | AED-15 | T011-T017 |
| ASR-087 | `aemusa_ms_decision_player_authorized` | 玩家决定 | country | flag | no | 玩家授权结算 | 存档永久 | 与 player_refused 互斥 | AED-15-20 | T014/T015 |
| ASR-088 | `aemusa_ms_decision_player_refused` | 玩家决定 | country | flag | no | 玩家拒绝结算 | 存档永久 | 与 player_authorized 互斥 | AED-15-20／NT-10 | T012/T017 |
| ASR-089 | `aemusa_ms_decision_aemusa_accepted` | 角色决定 | country | flag | no | 爱缪莎决定结算 | 存档永久 | 玩家已授权；与 refused 互斥 | AED-15-30 | T015/T017 |
| ASR-090 | `aemusa_ms_decision_aemusa_refused` | 角色决定 | country | flag | no | 爱缪莎决定结算 | 存档永久 | 玩家已授权；与 accepted 互斥 | AED-15-30／NT-20 | T013/T017 |

语义所有者为“玩家决定”或“角色决定”不要求把 flag 放在不稳定对象上；未来可由玩家国家保存权威事实，但只能由对应接口写入。

## 8. 暂停、冲突、结局与尾声

| 登记号 | 候选 key | 所有者 | scope | 类型 | 默认值 | 合法写入接口 | 生命周期 | 互斥／前置 | 对应规划 | 测试 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ASR-100 | `aemusa_ms_country_pause_active` | 历史进度 | country | flag | no | 暂停／恢复接口 | 可恢复 | 不能代表永久拒绝 | 跨章 | T004/T011 |
| ASR-101 | `aemusa_ms_country_pause_reason_index` | 历史进度 | country | variable | 0 | 暂停／恢复接口 | 可恢复 | 与 active 一致 | 跨章 | T004/T011 |
| ASR-102 | `aemusa_ms_country_consistency_conflict_active` | 一致性审计 | country | flag | no | 审计器 | 直到专项修复 | 不能通过普通恢复清除 | 全线 | T017 |
| ASR-103 | `aemusa_ms_country_consistency_conflict_index` | 一致性审计 | country | variable | 0 | 审计器 | 直到专项修复 | 必须对应可解释冲突 | 全线 | T017 |
| ASR-104 | `aemusa_ms_country_ending_non_transform_player_refusal_settled` | 结局 | country | flag | no | NT-10 唯一结算 | 存档永久 | 与其他结局互斥 | AED-NT-10 | T012/T017 |
| ASR-105 | `aemusa_ms_country_ending_non_transform_aemusa_refusal_settled` | 结局 | country | flag | no | NT-20 唯一结算 | 存档永久 | 与其他结局互斥 | AED-NT-20 | T013/T017 |
| ASR-106 | `aemusa_ms_country_ending_fate_sovereign_settled` | 结局 | country | flag | no | AED-16-10 唯一结算 | 存档永久 | 双方同意且全资格满足 | AED-16-10 | T015-T017 |
| ASR-107 | `aemusa_ms_country_fate_sovereign_authority_active` | 终局权限 | country | flag | no | AED-16-10 权限结算 | 存档永久 | ASR-106 同时成立 | AED-16-10 | T010/T016 |
| ASR-108 | `aemusa_ms_country_epilogue_tone_index` | 尾声历史 | country | variable | 0 | 尾声语气审计 | 存档永久 | 仅成功结局；值不得影响奖励 | AED-EPI-00 | T018 |
| ASR-109 | `aemusa_ms_country_epilogue_settled` | 尾声历史 | country | flag | no | AED-EPI-20 唯一结算 | 存档永久 | 成功结局和语气已锁定 | AED-EPI | T016/T018 |

## 9. 保存目标与非权威表现状态

| 登记号 | 候选 key | 所有者 | scope | 类型 | 默认值 | 合法写入接口 | 生命周期 | 互斥／前置 | 对应规划 | 测试 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ASR-120 | `aemusa_ms_aemusa_leader_target` | 角色定位 | saved target | target | none | 角色接入／恢复接口 | 可替换 | 不能证明路线进度 | 全线 | T003/T004 |
| ASR-121 | `aemusa_ms_current_scene_target` | 临时表现 | saved target | target | none | 场景表现接口 | 临时 | 缺失时从权威账本恢复表现 | 跨章 | T004 |
| ASR-122 | `aemusa_ms_current_anchor_target` | 专属危机表现 | saved target | target | none | 锚点状态机 | 锚点生命周期 | 不能单独证明锚点结果 | AED-12／13 | T006/T008 |
| ASR-123 | `aemusa_ms_megastructure_target` | 专属危机表现 | saved target | target | none | 巨构接入／恢复接口 | 可替换 | 所有权变化不删除资料 | AED-12-40 | T007 |
| ASR-124 | `aemusa_ms_country_presentation_replay_active_temp` | 临时表现 | country | flag | no | 表现重放接口 | 临时 | 不得触发选择和结算 | 全线 | T003/T004 |

## 10. 唯一结算模式

所有一次性结算使用：

```text
aemusa_ms_country_settlement_<object>_done
```

模式必须在代码阶段展开为显式登记项，至少覆盖：

- 每个 AED 事件簇；
- 章节和幕完成；
- 失落帝国战争结果映射；
- 原版天灾路线锁定和完成；
- 专属危机初始化、胜利／失败；
- 永久损失和锚点结果；
- 玩家和爱缪莎的四种来源决定；
- 两种非转变结局；
- 命运主宰身份和权限；
- 尾声语气和 1.0 路线完成；
- 一次性奖励、解锁与公开信息升级。

结算保护 key 与结果事实必须同时存在：前者证明“已执行一次”，后者证明“执行结果是什么”。

## 11. 状态转移审计规则

1. 任何写入必须记录旧状态、目标状态、写入接口和规划编号。
2. variable 只能使用登记的枚举值，不允许临时增加未记录数字。
3. 永久 flag 只能由明确接口写入，不由窗口显示或对象存在推断。
4. 互斥结果写入前必须检查竞争结果不存在。
5. 写入后立即执行局部一致性审计；失败时不得继续不可逆推进。
6. 调试注入必须设置独立测试标记，不能作为正常路线验收证据。
7. 迁移只能从旧存档中可证明的事实恢复状态，不能猜测玩家决定。

## 12. ASR-R001 审核记录

请审核：

1. 是否批准 ASR-001 至 ASR-124 的核心状态登记范围及登记字段；
2. 是否批准事件簇四阶段、章节和幕使用模式登记，并在代码阶段展开为显式 key；
3. 是否批准失落帝国战争、单一原版天灾与专属危机使用分离且单向推进的历史状态；
4. 是否批准文明选择、关系责任、永久损失、弱点资料和巨构占领状态各自独立保存；
5. 是否批准真相层级、终局资格和双方决定使用独立事实，不从等级、危机或对象存在推导；
6. 是否批准暂停、硬冲突、三种结局、终局权限和尾声使用互斥、可审计状态；
7. 是否批准 saved target 和表现状态均不具备路线权威，缺失时只能恢复表现或硬阻断；
8. 是否确认所有 key 仍是候选，获批后还需代码阶段展开、作用域验证和逐项实现授权。

审核结果：2026-08-16 用户明确批准。ASR-001 至 ASR-124 核心登记范围、事件簇四阶段模式、章节与幕状态、失落帝国战争／单一原版天灾／专属危机历史、文明选择、关系责任、永久损失、危机资料、真相层级、终局资格、双方决定、暂停、冲突、三种结局、终局权限、尾声和非权威保存目标的登记规则正式锁定。

本文曾作为爱缪莎 1.0 主线候选状态登记基线。经用户单独授权的 AWP-00 已将模式和候选 key 展开至扩展登记表，AWP-01 随后也获得单独授权并实现最小写入接口。总体 `implementation_authorized` 仍保持 `false`；AWP-02 及后续写入接口仍须按工作包单独批准。

## 13. AWP-00 实施记录

2026-08-16，用户单独授权执行 AWP-00。此次授权只覆盖状态展开、只读一致性审计和测试诊断，不覆盖 AWP-01 或任何章节剧情实现。

### 13.1 正式登记输出

机器可审查的正式清单位于：

- [`aemusa_main_story_state_registry_expanded_v1.0.csv`](aemusa_main_story_state_registry_expanded_v1.0.csv)。

清单共登记 650 个显式状态项，其中包括：

- 103 个 AED 事件簇的 412 个四阶段事实；
- 103 个与结果事实分离的事件簇结算保护；
- 18 个章节结果与 18 个章节结算保护，其中 `CH-00` 即序章，尾声使用独立 `epilogue` 命名；
- 6 个幕结果与 6 个幕结算保护；
- ASR-001 至 ASR-124 中所有非模式核心状态；
- 战争、原版天灾、专属危机、永久损失、双方决定、三种结局、命运主宰权限、尾声和 1.0 路线完成的关键一次性结算保护。

### 13.2 隔离待审枚举

AWP-01 已批准路线版本编号 `1`，并将 `ASR-002` 更新为 `formal_awp_01`。目前仍有以下 6 项保留正式 key，但精确数值映射尚未由上游设计批准，因此标记为 `reserved_pending_enum_review`，任何后续工作包在审核完成前都不得写入：

1. 行动节奏；
2. 信息治理策略；
3. 责任半径；
4. 中央庭真相可见层；
5. 爱缪莎真相可见层；
6. 一致性硬冲突编号。

这种隔离不是默认值，也不是允许实现阶段自行补充；它用于防止代码根据叙事词语猜测枚举。

### 13.3 只读审计输出

- `mod/common/scripted_triggers/aemusa_ms_state_audit_triggers.txt`：登记枚举、战争／危机历史、资料与损失、真相互认、双方决定、终局资格、三结局、权限、尾声、暂停和冲突一致性检查；
- `mod/common/scripted_effects/aemusa_ms_state_audit_effects.txt`：只向 `game.log` 输出逐组 `PASS`／`FAIL`，不写入任何路线事实。

AWP-00 没有创建事件、on_action、本地化、危机、舰船或巨构实现。2026-08-16 最终运行时审计获得 11 项 `PASS`、0 项 `FAIL`，且没有本包解析错误。总体 `implementation_authorized` 继续保持 `false`，只记录 AWP-00 已单独获准并验收完成。

## 14. AWP-01 实施记录

2026-08-16，用户单独授权执行 AWP-01。此次授权只覆盖主线最小运行骨架，不覆盖序章、正式对白、奖励、危机、舰船、巨构或结局实现。

### 14.1 已建立接口

- 路线版本固定为 `1`；仅玩家控制且主物种为神器使的国家可以执行一次性初始化；
- 新增事件簇“开始／完成／唯一结算”三个显式生命周期接口，所有参数必须使用扩展登记表中的现有 key；
- 白夜馆新增只读主线入口，仅打开“序章之前”的骨架状态页，不写入事件簇、章节或结算事实；
- 新增基于 `AED-PRO-10` 的三步测试探针，仅供测试存档验证幂等性与结算保护；
- AWP-00 聚合审计增加路线版本检查，路线初始化后预期为 12 项 `PASS`、0 项 `FAIL`。

### 14.2 当前门禁状态

静态检查已经通过：650 项登记无重复、剩余待审枚举为 6 项、52 个直接读取或写入的主线状态 key 全部已登记、新增脚本无 BOM 且花括号匹配、本地化继续保留 UTF-8 BOM。

2026-08-16 的 Stellaris 4.4.3 运行日志确认：AWP-01 探针连续三次均为 3 项 `PASS`、0 项 `FAIL`，聚合审计为 12 项 `PASS`、0 项 `FAIL`，相关 `error.log` 错误为 0。随后人工确认白夜馆“爱缪莎主线”入口与序章前只读状态页正常显示，保存并读档后入口和状态仍然正常。因此 AWP-01 状态正式更新为 `completed_runtime_pass`。

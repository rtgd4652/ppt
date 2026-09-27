---
title: "AWP-03 4.5.1 战争运行测试记录"
work_package: AWP-03
runtime_status: in_progress
war_callback_status: scripted_start_observed
last_updated: 2026-09-27
---

# AWP-03 4.5.1 战争运行测试记录

## 无战争基线

2026-09-27 12:21（北京时间），仅启用本 Mod 的 Stellaris 4.5.1 在 `2215.11.25` 正常档暂停。用户在玩家国家作用域执行只读命令 `effect aemusa_ms_log_awp_03_audit = yes`。`game.log` 同时出现 `PASS|awp_03_registered_state`、`WAIT|awp_03_war_not_started`、`WAIT|awp_03_qualified_war_not_started` 和 `WAIT|awp_03_no_war_result`；审计以 `writes=none` 结束。此结果只证明开战前账本一致，未证明战争回调或第四至第六章运行通过。

游戏仍停在原日期、保持暂停。原正常档 `2215.11.25.sav` 与其副本 SHA-256 均为 `75D5AA8188649BD399003C16BFB0FF11E4C11E491C3170BD95993A8152F6C94C`。审计后的 `game.log` SHA-256 为 `2A6186EFC460AF91BBB4AEC58F947E21FF7F52A376563A98AE0577E9079C844A`；`dlc_load.json` 只含 `mod/aemusa_artifact_user.mod`。存档、加载配置及日志副本保留在本地忽略目录 `temp/awp03-451-20260927/run-1225-war-test-prep/`。

## 隔离档的脚本开战探针

12:32，用户在暂停的正常档中用控制台调用原版 `set_country_type` 和 `declare_war`，使唯一失落帝国转为 `awakened_fallen_empire` 后作为主攻方向玩家宣战。`on_war_beginning` 写出 `qualified_fe_war_started`。随后只读审计新增 `OBSERVED|awp_03_war_attacker_locked` 和 `OBSERVED|awp_03_qualified_war_active`。重复的审计文本未再次出现在日志中，因此以战前完整审计、新出现的两行和存档状态共同判读。

用户另存 `AWP03-war-start-2215.sav`；原 `2215.11.25.sav` 哈希未变。新档 SHA-256 为 `CE63A19A5D7AFE6FECD5B9FE60EAC7407F1E71AF3F388A487B14C1B22E397156`。从新档 `gamestate` 读取到战争 `0` 的主攻国家 `16777223`、主防玩家 `0`、原版战胜目标 `wg_ae_domination`，战争对象持有 `aemusa_ms_qualified_fe_war` 标记；玩家国家有开战旗标、第四章索引 `4`，全局事件目标指向同一攻击者。新档及战后日志副本在 `temp/awp03-451-20260927/run-1232-script-war/`；审计后日志 SHA-256 为 `D1EBFA9B5081961896CB4C662C4349B4B3EABBC9C6EC3D56051BA571B9FC3571`。

同一开战瞬间 `on_entering_war` 先写出 `late_join_unqualified`，随后才写合格开战，说明“晚加入”旁证把原始防守参战误记为晚加入。该旗标不参与资格和章节门禁。已从源代码移除 `.611` 及其回调注册，并将登记项标为旧测试档遗留；当前游戏进程仍使用启动时加载的旧脚本，修复后的运行表现须重启验证。

游戏内通过白夜馆正常入口打开第四章首窗“旧日目光”，正文只陈述觉醒失落帝国主攻、玩家原始主防，并明确保留外交要求和动机未知。随后 `.700`、`.710`、`.720`、`.730`、`.740` 五窗连续执行；`.730` 选第一项“立即公开已核实事实”，结算后没有直接生成战争结果。独立存档 `AWP03-ch04-done-2215.sav` 的 SHA-256 为 `DCCB4444D957FB83F65A05E8FD7CDE0D4E66BF07DFCFB661CFBBC4A1BE62B0E5`：第五章索引为 `5`，第四章完成和结算旗标各出现一次，首次公开选择值为 `1`，同场战争标记仍在，玩家胜利旗标不存在。

再次经白夜馆入口进入第五章，日志依次出现 `.800`、`.810`、`.820`；`.820` 选第一项后转到等待页 `.104`，没有直接跳到 `.830` 或第六章。但独立存档 `AWP03-ch05-wait-2216.sav`（SHA-256 `4D8AEEEC4EED4BF8595715839BFF7F54611600C3B279D24DE910CBE827C760FE`）中，三个第五章事件簇均无 `started`／`settled` 旗标，战时优先级变量也不存在。窗口显示不能证明选项写入；这是待定位的运行缺陷，第五章尚未通过。12:40 写出的原版 `autosave_2216.01.01.sav`（SHA-256 `A87AE6C3A4120B1B46F0173007061E6059618B998B0B8BBE040C25F68DA26415`）同样没有第五章旗标或战时优先级变量，排除仅一个手动存档写出异常。两档副本均存于上述本地忽略证据目录。12:45 的只读控制台探针记录 `AEMUSA-MS|PROBE|can_enter_05_yes`，说明当前玩家至少满足第五章入口；下一步需在第五章首窗打开而选项未点时另存，检查 `immediate` 是否写入事件簇进行中状态。

## 待验证

脚本触发的战争只验证引擎回调路径，不计作自然外交与宣战的 FEA-01～03 验收。其后仍须在同一战争的实际胜利回调中核对第六章资格，并独立测试战败、维持现状、读档和反例。当前 FEA-01～06 与新章节运行验收均未通过。

---
title: "AWP-03 4.5.1 战争运行测试记录"
work_package: AWP-03
runtime_status: in_progress
war_callback_status: not_observed
last_updated: 2026-09-27
---

# AWP-03 4.5.1 战争运行测试记录

## 无战争基线

2026-09-27 12:21（北京时间），仅启用本 Mod 的 Stellaris 4.5.1 在 `2215.11.25` 正常档暂停。用户在玩家国家作用域执行只读命令 `effect aemusa_ms_log_awp_03_audit = yes`。`game.log` 同时出现 `PASS|awp_03_registered_state`、`WAIT|awp_03_war_not_started`、`WAIT|awp_03_qualified_war_not_started` 和 `WAIT|awp_03_no_war_result`；审计以 `writes=none` 结束。此结果只证明开战前账本一致，未证明战争回调或第四至第六章运行通过。

游戏仍停在原日期、保持暂停。原正常档 `2215.11.25.sav` 与其副本 SHA-256 均为 `75D5AA8188649BD399003C16BFB0FF11E4C11E491C3170BD95993A8152F6C94C`。审计后的 `game.log` SHA-256 为 `2A6186EFC460AF91BBB4AEC58F947E21FF7F52A376563A98AE0577E9079C844A`；`dlc_load.json` 只含 `mod/aemusa_artifact_user.mod`。存档、加载配置及日志副本保留在本地忽略目录 `temp/awp03-451-20260927/run-1225-war-test-prep/`。

## 待验证

下一步在隔离测试过程中，让觉醒失落帝国作为原始攻击战争领袖向玩家直接宣战，检查 `on_war_beginning` 的 `qualified_fe_war_started`、战争实例标记和只读审计，再核对第四、五章窗口。脚本触发的战争只验证引擎回调路径，不计作自然外交与宣战的 FEA-01～03 验收。其后仍须在同一战争的实际胜利回调中核对第六章资格，并独立测试战败、维持现状、读档和反例。当前 FEA-01～06 与新章节运行验收均未通过。

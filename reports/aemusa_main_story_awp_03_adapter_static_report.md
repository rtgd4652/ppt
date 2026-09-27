---
title: "AWP-03 外交与战争事实适配首批静态报告"
work_package: AWP-03
status: implemented_static_pass_runtime_partial
runtime_status: controlled_start_victory_chapters_04_06_reloaded_partial
last_updated: 2026-09-27
---

# AWP-03 外交与战争事实适配首批静态报告

## 范围与判定

用户已单独选择推进 AWP-03，并批准严格的 FEA-02／03 资格；随后明确“不需要精确回调，只要确定开战和胜利就可以了”。修订后只要求觉醒失落帝国作为原始攻击战争领袖直接对玩家原始防守领袖开战，并以玩家作为胜方战争领袖赢得**同一战争**作为第六章资格。此前的外交要求锁定不再是前置。盟友参战、玩家主动进攻、战败与维持现状记录旁证或真实结果。晚加入不能仅凭 `on_entering_war` 判定。

这批代码只接入原版外交回应旁证和战争回调；没有第四至第六章剧情窗口、章节结算、战争创建或奖励。第四章改为开战后入口，不能宣称此前发生过某项具体外交要求。

## 已接入的原版事实

| 来源 | 写入 | 边界 |
| --- | --- | --- |
| 原版失落帝国对玩家的三种要求回应关系修正 | 候选主体唯一时记录可选外交旁证 | 不参与章节或战争资格；多个主体时只记歧义，不能还原具体要求 ID／正文；原版 `.4`～`.8` 的接受一般要求分支没有写这三种修正 |
| `on_war_beginning` | 从战争对象识别双方原始战争领袖；直接保存觉醒失落帝国攻击者、给合格战争打标；另记玩家进攻、盟友防守或重复开战 | 不要求先锁定外交主体或结算第四章；排除代理战争；同一玩家路线目前只锁定第一场合格战争 |
| `on_entering_war` | 2026-09-27 运行纠错后停用 | 原始开战时也会触发；旧测试档的“晚加入”旗标可能误标，不参与合格开战判定 |
| `on_war_won`／`on_war_lost` | 同一战争的胜利或战败与真实结束事实 | 只以战争对象标记关联实例；`on_war_ended` 不承担结果判定 |
| `on_status_quo`／`on_status_quo_forced` | 同一战争的维持现状与真实结束事实 | 不等于玩家胜利 |

`aemusa_ms_country_has_valid_fe_intervention_source` 仅检查可选外交旁证的枚举与歧义状态；`aemusa_ms_country_has_valid_fallen_empire_war_history` 检查结果互斥、完成必须有结果及开战时路线已初始化。战争、结果与第四章剧情状态分离；回调本身不推进章节。

另有只读 `aemusa_ms_log_awp_03_audit`，供隔离测试存档在玩家国家作用域输出 `PASS`、`OBSERVED`、`WAIT`、`BLOCK` 与 `CHECK`；它会检查战争攻击者目标是否存在，不把可选外交旁证的歧义当作阻断。本首批静态快照时该命令尚未在游戏执行；后续已在战前、战中和完成态执行，详见[运行记录](aemusa_main_story_awp_03_runtime_2026-09-27.md)。审计日志不能代替原版战争回调证据。

## 静态验证

2026-09-27，在项目根目录执行：

- `G:/python/python.exe -B tools/validation/check_mod.py --game-dir F:/steam/steamapps/common/Stellaris`：PASS，54 个脚本文件、63 个事件、671 个登记状态。
- `G:/python/python.exe -B -m unittest discover -s tools/validation/tests`：20 项通过。
- `git diff --check`：未发现空白格式错误。

原版回调作用域和关系修正写入点来自本机 4.5.1 的 `common/on_actions/00_on_actions.txt`、`events/fallen_empire_events.txt`、`events/fallen_empire_tasks_events.txt`；动态全局事件目标与战争标记语法在本机原版脚本中有对应使用例。静态通过只证明本项目可解析的结构与引用，不证明引擎会按预期触发。

10:41 的首批适配快照在 4.5.1（`f63e`）冷启动；10:57 加上歧义保护与来源审计（`477c`）；11:05 加入只读审计命令（`2f02`）；用户取消精确外交前置后，11:25 将攻击者改为从战争双方直接锁定，并第四次冷启动（`c957`）。四次均读入 `2215.11.25.sav` 并保持暂停；载入前后原档 SHA-256 均为 `75D5AA8188649BD399003C16BFB0FF11E4C11E491C3170BD95993A8152F6C94C`。四批 `error.log` 均未检出 AWP-03、未知触发器或相关作用域报错；`game.log` 尚无 AWP-03 回调记录。证据在本地忽略目录 `temp/awp03-451-20260927/run-1041-cold-load/`、`run-1057-cold-load/`、`run-1105-cold-load/` 与 `run-1125-cold-load/`。冷启动和旧档载入只证明脚本能装载，不等于月度脉冲、诊断命令执行或战争回调已通过。

最新批次的 `dlc_load.json` 仅启用 `mod/aemusa_artifact_user.mod`；复制件 SHA-256：`dlc_load.json` 为 `FC55ADE4898885E609B2D194B09096AFEFB535AB3E58D854D5621779C06B3490`，`error.log` 为 `A6C83A66A5FF0144C6F18740680952C7BA652D93294DED54E877E4C49440B101`，`game.log` 为 `6D94501B3482F9E19E0AD7BE39EE6B0D018BE9601C0A6C1577D001453EA14855`。这些是测试快照标识，不代表零错误；检索范围仅是本包及脚本加载相关报错。

## 运行追补与未验证项

2026-09-27，隔离档的受控脚本开战触发 `qualified_fe_war_started`；战中存档确认战争标记、玩家开战旗标及攻击者目标。控制台令该同场战争中的失落帝国投降后，玩家胜利回调触发；第四至第六章按正常窗口依次结算，完成态读档账本一致。这些结果修正了本报告早期“尚未测试”的时间截面，但不构成自然外交、宣战或胜利验收。`on_entering_war` 在原始开战瞬间误写晚加入旗标，源代码现已停用该旁证，须从战前档重开战验证。首轮两份第五章存档缺状态的原因仍未知，后续逐窗重试未复现。旧进程的战后审计因攻击者灭国误报 `BLOCK`，只读审计代码已修并通过 14:26 新进程冷重启复核。FEA-01～06 尚未整项通过；战败、维持现状、多战争并发与自然战争仍待核对。详见[运行记录](aemusa_main_story_awp_03_runtime_2026-09-27.md)。

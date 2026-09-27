# AWP-03 同场开战通知运行重放

此目录是可审查的隔离测试夹具，不是正式 Mod 内容。仅将其中两份 `.txt` 临时复制到 `mod/` 的对应相对路径，再完整重启游戏。不要发布带夹具的构建。

测试基线须为玩家主防的一场仍活跃、已登记的合格觉醒失落帝国战争，且没有“防守受阻”或战争结束旗标。原档保留，只载入它的独立副本。单人读档回调会在暂停状态重放一次自定义 `on_action`，列表直接引用正式 `aemusa_ms.610`，不复制其实现，也不调用原版 `on_war_beginning` 列表。

每轮保存并归档日志和结果副本，完整退出游戏后冷启动，再载入上一轮结果，连续三轮。初版在同一执行链派发三次时只出现一条正对照日志；同进程再次载档也没有新增夹具日志。原因未定，均不计为额外执行证据，因此每轮使用独立进程和日志。

本机 4.5.1 依据：`common/on_actions/00_on_actions.txt` 的 `on_single_player_save_game_load` 为无作用域；游戏导出的 `script_documentation/effects.log` 定义 `fire_on_action` 的 `scopes` 和国家作用域的 `random_war`。国家事件建立玩家 `root`，在战争内返回玩家后以 `from = prev` 传入同一战争。

运行必须同时确认：

- 每轮一组 `load_fixture`、`begin`、`dispatch` 和 `end`。
- 每轮正对照 `PASS|player_and_qualified_war_scope` 恰好一次，三轮各有独立记录，证明实际处理了正确作用域。
- 负对照 `FAIL|trigger_was_bypassed` 为零，证明事件触发条件没有被绕过。
- 无任何 `AEMUSA-REPLAY|FAIL`、重复 `qualified_fe_war_started` 或 `defense_blocked_by_precondition`。
- 前后只读审计一致；另存隔离档后完整对照 `aemusa_ms_` 主线状态、攻击者目标及战争标记，不能只看窗口。

测试完成后移除 `mod/common/on_actions/zz_aemusa_awp03_replay_fixture.txt` 和 `mod/events/zz_aemusa_awp03_replay_fixture_events.txt`，冷重启正式构建并重新载入保留基线。确认日志没有夹具条目，正式适配器文件未改变。

本测试证明已有合格战争的重复通知在真实引擎内被忽略；它不证明自然宣战、盟友参战或重复结束回调通过。

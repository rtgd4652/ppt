# 第三节点至终章与白夜馆交接核对（2026-11-15）

核对基线为 `c87691f`。第二节点已有成功归档实机证据；本轮只检查第三节点之后的生产事件、条件和效果调用链，未操作游戏或存档。未发现需要修改生产代码的断链，第三节点与完整终局的实际运行仍待主线续玩确认。

## 第三次归档后的入口

| 正常页面与选择 | 生产行为与条件 |
| --- | --- |
| `aemusa_exclusive.30.archive` 归档 | 需当前节点已有结果、真实击破、现场勘查证据和解析3/3。归档只加一次，阶段从30变40；第三次归档后由 `.1` 优先转到 `.50`，不会再显示下一节点。 |
| `.50.reopen`「爱缪莎：在这些现实条件上，重新开放非毁灭的未来。」 | 需归档3、真实击破3、弱点已验证、枢纽仍运行、旗舰仍在当前节点；另行记录未来重开，不代替最终身份决定。 |
| `.60.settle`「确认危机结束，进入代价清点。」 | 重新检查双计数和未来重开记录，一次写入共同胜利三旗、锁定节点结果，专属危机阶段变60。此时章节仍是13。 |
| `.80.record`「记录代价，让众人先恢复。」 | 正式结算第13章并进入章节14、完成第五阶段。随后 `.90` 可进入 `aemusa_finale.1`，由其路由到第14章复盘。 |

源码：[危机事件](../mod/events/aemusa_ms_exclusive_events.txt)、[归档与胜利结算](../mod/common/scripted_effects/aemusa_ms_exclusive_effects.txt)、[重开未来条件](../mod/common/scripted_triggers/aemusa_ms_exclusive_triggers.txt)。危机结算不会直接写入玩家最终授权、爱缪莎最终接受或正式转变。

第14章前半复盘读取共同胜利和历史记录；后半责任复核及最终决定还需基础等级30和既有责任条件。低于30级时已有正常研修入口，每次500凝聚力、200能源、180天后提升一级；不应将这道门槛误判为第三节点断链。[终章条件](../mod/common/scripted_triggers/aemusa_ms_finale_triggers.txt)、[研修效果](../mod/common/scripted_effects/aemusa_ms_finale_effects.txt)。

## 三种结局与交接

玩家拒绝、爱缪莎拒绝在各自正式结算页完成后，均可路由到 `aemusa_finale.200`。命运主宰路线在正式转变、十六章和尾声结算后路由到同一结果页。三条路各自检查原有决定与记录，不相互补写身份；已归档结论的重读不要求爱缪莎仍在场。[终章事件](../mod/events/aemusa_ms_finale_events.txt)

第14章首个复盘页、正式结局结果页以及白夜馆“回忆”都指向 `aemusa_finale.210`。交接资格仅依本国的共同胜利三旗，不要求个人转变，也不依赖仍有领袖或仍在现场。只有个人结论、缺共同胜利记录的旧档只能重读个人结果，不会因此取得公共奖励。[公共交接条件](../mod/common/scripted_triggers/artifact_postcrisis_archive_triggers.txt)、[白夜馆入口](../mod/events/aemusa_dialogue_events.txt)

交接单直接读取本国击破、归档、解放、永久损失四项计数；上述结尾流程不重置它们。旧档缺明细时展示胜利摘要，不将缺失值补成零。[战果文案选择](../mod/common/scripted_loc/artifact_postcrisis_handover_loc.txt)

## 验证范围与下一次观察

本轮生产脚本和测试未变，沿用已有危机末段、三结局及交接回归；不重复全套检查。对应保护见 `test_awp06_crisis_state.py` 的最终结算测试、`test_milestone2_finale_state.py` 的三条结局测试、`test_postcrisis_handover.py` 的公共入口与旧档计数测试。既有结果见[交接实施与代表实机](postcrisis_ending_handover_2026-11-09.md)、[核心机制记录](aemusa_exclusive_core_pressure_2026-11-09.md)。

后续最小实机观察可并入一次正常续玩：

1. 第三次归档后保留旗舰在当前节点，依次完成重开未来、危机结算和代价记录；应出现日志 `exclusive_crisis_settled`、`chapter_13_completed`，章节变14。
2. 从第14章复盘打开交接单，确认归档3、击破3，以及本次实际解放数和永久损失；不预设必须零损失。
3. 沿一条选定的合法结局完成后，再从白夜馆回忆重读同一战果。其他结局先复用既有代码回归，不为此次观察重新跑三条长线。

新档实际载回、第三节点非零历史损失传递与完整终局通关均不因本报告升级为实机通过。

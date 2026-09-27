---
title: "AWP-03 4.5.1 战争运行测试记录"
work_package: AWP-03
runtime_status: in_progress
war_callback_status: scripted_victory_observed
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

再次经白夜馆入口进入第五章，日志依次出现 `.800`、`.810`、`.820`；`.820` 选第一项后转到等待页 `.104`，没有直接跳到 `.830` 或第六章。但独立存档 `AWP03-ch05-wait-2216.sav`（SHA-256 `4D8AEEEC4EED4BF8595715839BFF7F54611600C3B279D24DE910CBE827C760FE`）中，三个第五章事件簇均无 `started`／`settled` 旗标，战时优先级变量也不存在。12:40 写出的原版 `autosave_2216.01.01.sav`（SHA-256 `A87AE6C3A4120B1B46F0173007061E6059618B998B0B8BBE040C25F68DA26415`）同样没有第五章旗标或战时优先级变量。窗口日志与这两份存档存在未解释的状态差异，不能以窗口显示代替账本验证。两档副本均存于上述本地忽略证据目录。12:45 的只读控制台探针记录 `AEMUSA-MS|PROBE|can_enter_05_yes`，说明当前玩家满足第五章入口。

## 第五章逐窗复测

13:03 重新经白夜馆进入第五章，停在首窗另存 `AWP03-ch05-entry-probe-2216.sav`（SHA-256 `DEFEA99D7D6E6261BCA59E3ADE8654C2E19A48F4E131E490AAB8760A5E797F68`）。存档已有 AED-05-00 的 `started` 与 `in_progress`，没有完成旗标，确认首窗 `immediate` 正常写入。点击首窗唯一选项、停在第二窗另存 `AWP03-ch05-00-settled-2216.sav`（`21CD33DF6D1A4A7ED56BD97C2325B9522103881C25286E7FCD94ABD3BB27E752`）：05-00 唯一结算，05-10 进入进行中。点击第二窗唯一选项、停在第三窗另存 `AWP03-ch05-10-settled-2216.sav`（`025CFD621155DA17EA532915F1D08FF04BBB2B91B263EABA723F74CF7732C5FD`）：05-10 唯一结算，05-20 进入进行中。

第三窗选第一项“平民优先”，游戏显示“战争仍由现实决定”的等待页。用户此时以默认日期名保存 `2216.03.12.sav`（SHA-256 `90E68A539BA04BD99232FEAE54207B6AD8C60F5B54B2C1184DB7E51B3D683E69`）；证据副本另名 `AWP03-ch05-20-wait-2216-from-2216.03.12.sav`。存档有 05-00／10／20 三簇结算，战时优先级为 `1`，同场战争标记仍在，玩家胜利旗标不存在。关闭等待页并载入这个档后，“战争仍由现实决定”窗口直接恢复；无需重新激活白夜馆法令。当前逐窗及读档流程没有复现先前的状态缺失，但第一次异常原因仍未知；第五章的胜利后半段尚未验证。

## 同场受控胜利回调

本机控制台 `help surrender` 显示语法 `surrender [<country_id>] [<war_id>]`。第一次输入存档中的 Full ID `16777223` 时，控制台明确报 `Invalid arg <COUNTRY ID>`，战争未结束。随后游戏内 `debugtooltip` 在攻击方国旗上显示 `Index: 7, Full ID: 16777223`；改用 `surrender 7 0`。13:16:31 `game.log` 写出 `AEMUSA-MS|AWP-03|qualified_fe_war_player_victory`，说明同一带标记战争的胜利回调已触发。原版战争结束后先弹出“屏障星球”事件。该控制台结果只证明回调路径，不替代自然战争胜利验收。

用户在原版事件仍打开、游戏暂停时另存 `AWP03-war-victory-2216.sav`；原档与证据副本 SHA-256 同为 `55735AF5616A02C9E0F0A8E41296EFBB91D8DCFCFE2FD8FF6B77D3FC1F5CA55E`。`gamestate` 中战争 `0` 为 `attackers_surrendered=yes`、`end=yes`，保留其 `aemusa_ms_qualified_fe_war` 标记；玩家国家的 `aemusa_ms_country_history_fallen_empire_war_completed` 和 `aemusa_ms_country_fe_war_player_victory` 各出现一次，战败、维持现状旗标均不存在。第五章 05-00／10／20 的结算旗标和战时优先级 `1` 保留，章节索引仍为 `5`，05-30／40 与第六章状态尚未写入。战前 `2216.03.12.sav` 及原正常档 `2215.11.25.sav` 哈希未变。胜利后的主线窗口还未打开，不能仅凭回调把第五或第六章记为通过。

## 待验证

脚本触发的战争只验证引擎回调路径，不计作自然外交与宣战的 FEA-01～03 验收。下一步经正常入口核对第五章战后两簇、第六章资格及读档，并独立测试战败、维持现状和其他反例。当前 FEA-01～06 与第四至第六章的整项运行验收均未通过。

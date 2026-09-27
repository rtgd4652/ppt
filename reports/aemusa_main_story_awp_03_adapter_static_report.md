---
title: "AWP-03 外交与战争事实适配首批静态报告"
work_package: AWP-03
status: implemented_static_pass_runtime_pending
runtime_status: not_tested
last_updated: 2026-09-27
---

# AWP-03 外交与战争事实适配首批静态报告

## 范围与判定

用户已单独选择推进 AWP-03，并批准严格的 FEA-02／03 资格：只有已锁定的觉醒失落帝国作为原始攻击领袖直接对玩家原始防守领袖开战，才能记录合格战争；只有玩家作为胜方战争领袖赢得同一战争，才能获得第六章资格。盟友参战、玩家主动进攻、晚加入、战败与维持现状只记录事实。

这批代码只接入原版外交回应和战争回调；没有第四至第六章剧情窗口、章节结算、战争创建或奖励。第四章的具体要求内容仍无可靠的原版脚本来源，因此 AED-04-00 保持阻断。

## 已接入的原版事实

| 来源 | 写入 | 边界 |
| --- | --- | --- |
| 原版失落帝国对玩家的三种要求回应关系修正 | 候选主体唯一时锁定该失落帝国、记录回应来源类型 | 多个主体时只记歧义；同一主体多种修正记“混合”；多个原版事件共用修正，不能还原具体要求 ID／正文；逐月检测可能错过短暂修正 |
| `on_war_beginning` | 合格战争对象标记及开始事实；另记玩家进攻、盟友防守或前置不满足 | 第四章必须已结算；双方原始战争领袖；目标为同一已觉醒主体；排除代理战争 |
| `on_entering_war` | 晚加入旁证 | 此回调无战争对象，不补写合格开战 |
| `on_war_won`／`on_war_lost` | 同一战争的胜利或战败与真实结束事实 | 只以战争对象标记关联实例；`on_war_ended` 不承担结果判定 |
| `on_status_quo`／`on_status_quo_forced` | 同一战争的维持现状与真实结束事实 | 不等于玩家胜利 |

`aemusa_ms_country_has_valid_fe_intervention_source` 检查来源枚举与歧义状态，`aemusa_ms_country_has_valid_fallen_empire_war_history` 检查结果互斥、完成必须有结果及开战必须在第四章之后。战争、结果与第四章剧情状态分离；回调本身不推进章节。

## 静态验证

2026-09-27，在项目根目录执行：

- `G:/python/python.exe -B tools/validation/check_mod.py --game-dir F:/steam/steamapps/common/Stellaris`：PASS，54 个脚本文件、63 个事件、670 个登记状态。
- `G:/python/python.exe -B -m unittest discover -s tools/validation/tests`：20 项通过。
- `git diff --check`：未发现空白格式错误。

原版回调作用域和关系修正写入点来自本机 4.5.1 的 `common/on_actions/00_on_actions.txt`、`events/fallen_empire_events.txt`、`events/fallen_empire_tasks_events.txt`；动态全局事件目标与战争标记语法在本机原版脚本中有对应使用例。静态通过只证明本项目可解析的结构与引用，不证明引擎会按预期触发。

10:41 的首批适配快照已在 4.5.1（主菜单校验码 `f63e`）冷启动；随后加上多主体歧义保护与来源审计，10:57 再次冷启动最新代码（校验码 `477c`）。两次均读入 `2215.11.25.sav` 并保持暂停；载入前后原档 SHA-256 均为 `75D5AA8188649BD399003C16BFB0FF11E4C11E491C3170BD95993A8152F6C94C`。两批 `error.log` 均未见 AWP-03、未知触发器或相关作用域报错；`game.log` 尚无 AWP-03 回调记录。证据复制在本地忽略目录 `temp/awp03-451-20260927/run-1041-cold-load/` 与 `run-1057-cold-load/`。冷启动和旧档载入只证明最新脚本能装载，不等于外交捕获、月度脉冲或战争回调已通过。

最新批次的 `dlc_load.json` 仅启用 `mod/aemusa_artifact_user.mod`；复制件 SHA-256：`dlc_load.json` 为 `FC55ADE4898885E609B2D194B09096AFEFB535AB3E58D854D5621779C06B3490`，`error.log` 为 `6892F506E6165C95808FE2864F438D93B508E6C02EBEBA67030FCD346C7F770B`，`game.log` 为 `0C1F55955926DC41373BBB9D9E6E9C995C0B0CEFC4E3194D6513D9FC5AFEA50A`。这些是测试快照标识，不代表零错误；检索范围仅是本包及脚本加载相关报错。

## 尚未验证

FEA-01～06、章节 T002～T004、外交修正的实际捕获、`@root` 目标跨读档、战争实例标记在胜利／战败／维持现状回调中的可见性，以及多战争并发，均未执行游戏内验证。第四章具体要求的精确来源也未解决。下一轮先定第四章口径，再用隔离测试档与游戏日志验证回调；正常存档不得用测试注入补写历史。

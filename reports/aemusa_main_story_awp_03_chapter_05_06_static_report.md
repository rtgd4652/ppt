---
title: "AWP-03 第五六章静态与载入冒烟报告"
work_package: AWP-03
scope: "AED-05-00～40；AED-06-00～90"
static_status: pass
load_smoke_status: pass
story_runtime_status: not_tested
war_callback_status: not_tested
last_updated: 2026-09-27
---

# AWP-03 第五六章静态与载入冒烟报告

## 实现范围

第五章在第四章已结算、合格战争已开始后进入。AED-05-00～20 记录开战事实、有限观测的停止条件和中央庭首次战时责任优先级。随后白夜馆停在同场胜利等待页；只有适配器在已标记战争的结果回调中写入玩家胜利，AED-05-30～40 才可结算。战败或维持现状只保留其真实结果，不能取得第六章资格。若胜利早于阅读第五章，原胜利事实也不被覆盖。

第六章要求第五章结算和同场胜利，AED-06-00～90 保存战后公开方式、恢复优先级、第二幕唯一结算和可停留的恢复期。安托涅瓦承担公开责任，爱缪莎仍无主动干涉权限。三处选择变量均首次写入后不可由旧窗口改选。章节事件不会制造战争、设定结果、清除损失或自动选择原版天灾。

用户取消精确外交回调的门槛，并将开战及同一战争胜利确定为必需事实。因此当前事件不凭空填写战役阶段、伤亡、撤离、盟约履行或补偿数字；旧制作卡的这些细粒度职责仍待可信事实接口，不算已实现。战时优先级与恢复优先级是责任记录，不会自行移动舰队或完成重建。

## 验证结果

- `G:/python/python.exe -B tools/validation/check_mod.py --game-dir F:/steam/steamapps/common/Stellaris`：PASS；57 个脚本文件、81 个事件、675 个本地化键、676 个登记状态。
- `G:/python/python.exe -B -m unittest discover -s tools/validation/tests`：30 项通过。新增账本测试覆盖无开战强制跳章阻断、战中等待、同场胜利放行、战败与维持现状阻断、三处选择不可重选、第二幕唯一结算与恢复期标记。测试注入战争旗标，不模拟 Stellaris 引擎或回调。
- `git diff --check`：无空白格式错误。
- 2026-09-27 11:55～11:56 北京时间，Stellaris 4.5.1 冷启动，主菜单校验码 `1d14`。`dlc_load.json` 仅启用 `mod/aemusa_artifact_user.mod`；原 `2215.11.25.sav` 成功载入，游戏保持暂停。`error.log` 检索 `aemusa_ms`、主线脚本、未知触发器／效果和作用域错误均无本包命中；`dependencies` 与 `remoe_file_id` 解析提示仍来自其他元数据。`game.log` 没有战争回调。证据副本位于忽略目录 `temp/awp03-451-20260927/run-1156-ch05-06-load/`。
- 原正常存档 SHA-256 仍为 `75D5AA8188649BD399003C16BFB0FF11E4C11E491C3170BD95993A8152F6C94C`。证据副本 SHA-256：`error.log` 为 `AD891C11B2E6EA453FDAD04674A25E9829CC110AA6EF52EBB97059A5B86D0796`，`game.log` 为 `3ABA704FBCAB39C2FC62DE6AD1110EB345487A41ED20CDC82919BD690E1466D3`，`dlc_load.json` 为 `FC55ADE4898885E609B2D194B09096AFEFB535AB3E58D854D5621779C06B3490`。

## 未通过的运行门禁

原正常档没有合格觉醒失落帝国战争，因此未观察到真实 `on_war_beginning`、`on_war_won`、败北或维持现状回调，也未在游戏内走过第四至第六章窗口、三处选择、读档恢复与恢复期。FEA-01～06 和章节 T002～T004 仍须在隔离测试档完成；静态检查与载入冒烟不能替代这些证据。下一步先取得同一场战争的开战及结果日志，再逐一核对路由、窗口显示和存档状态。

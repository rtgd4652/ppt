---
title: "AWP-03 第四章开战后入口静态与载入冒烟报告"
work_package: AWP-03
scope: "AED-04-00～40"
static_status: pass
load_smoke_status: pass
story_runtime_status: not_tested
war_callback_status: not_tested
last_updated: 2026-09-27
---

# AWP-03 第四章开战后入口静态与载入冒烟报告

## 实现范围

第四章现在从 `aemusa_ms_country_history_fallen_empire_war_started` 进入，并要求第三章已结算；没有合格开战时，白夜馆只显示等待页。AED-04-00～40 分别处理开战事实、知情权、证据边界、中央庭公开责任选择和章节结算。两种公开节奏只写入 `aemusa_ms_country_fe_war_public_accountability_index`，不制造战争、不写胜利或战败。旧事件窗口的选项副作用受事件簇生命周期门禁保护。

章节文本只确认战争适配器已记录的攻守事实，不叙述无法证明的战前外交要求、动机、战况或伤亡。第四章结算把章节索引从 4 推至 5，后续第五、第六章尚未接入。

## 验证结果

- `G:/python/python.exe -B tools/validation/check_mod.py --game-dir F:/steam/steamapps/common/Stellaris`：PASS；55 个脚本文件、69 个事件、637 个本地化键、672 个登记状态。
- `G:/python/python.exe -B -m unittest discover -s tools/validation/tests`：25 项通过，其中新增账本测试核对无战时等待、强制跳章阻断、两种公开选择、缺少选择时无法结算、旧窗口幂等、剧情不写战争结果，以及战前已获胜的历史不被覆盖。测试不模拟 Stellaris 引擎回调。
- `git diff --check`：无空白格式错误。
- 2026-09-27 11:44～11:46 北京时间，最终脚本在 Stellaris 4.5.1 冷启动，主菜单校验码 `375f`，仅启用 `mod/aemusa_artifact_user.mod`，读入 `2215.11.25.sav` 并保持暂停。`error.log` 检索 `aemusa_ms`、主线脚本、未知触发器／效果和作用域错误均无本包命中；出现的 `dependencies` 与 `remoe_file_id` 解析提示与本包路径无关。`game.log` 没有战争回调。证据副本位于忽略目录 `temp/awp03-451-20260927/run-1146-ch04-final-load/`。
- 原正常存档 SHA-256 仍为 `75D5AA8188649BD399003C16BFB0FF11E4C11E491C3170BD95993A8152F6C94C`。最终证据副本 SHA-256：`error.log` 为 `C267328CBE017AC7A4DCCE0E048012C36A0ADA3E6D78B15AF9C8B82D36DF094D`，`game.log` 为 `3B55CA9DD3AFD016C91BAD8D7931F70C3A47DE519CB2806198CDD56005BEE009`，`dlc_load.json` 为 `FC55ADE4898885E609B2D194B09096AFEFB535AB3E58D854D5621779C06B3490`。

## 未通过的门禁

当前正常档没有合格觉醒失落帝国战争。游戏内自动输入未被事件按钮接收，因此等待页、五个事件窗口、两种选择的实际显示与读档恢复尚无游戏内证据。FEA-01～06、战争实例标记跨回调及 T002～T004 均保持未测试；载入冒烟和账本测试不能替代它们。下一步需在隔离测试档取得真实开战及同一战争胜利或失败事实，再核对第四章正常流程与结果分支。

---
title: "AWP-03 战争事件链同类模组对照"
work_package: AWP-03
source_review_status: complete
script_change_status: not_needed_before_runtime_evidence
runtime_status: not_tested
last_updated: 2026-09-27
---

# AWP-03 战争事件链同类模组对照

## 对照材料与可用结论

本机 4.5.1 原版 `F:/steam/steamapps/common/Stellaris/common/on_actions/00_on_actions.txt` 给出的作用域是：`on_war_beginning` 对每个参战国触发，`Root` 是国家、`From` 是战争；`on_war_won` 的 `Root` 是胜方战争领袖、`FromFrom` 是战争；`on_war_lost` 与维持现状回调也携带战争对象。`on_war_ended` 只声明败方和主要胜方，没有战争对象，不能单独证明“同一场战争获胜”。原版 `events/nomads_events_1.txt` 的 `nomads.3075`、`.3076` 用 `FromFrom` 或 `FromFromFromFrom` 上的 `has_war_flag = nomad_mercs` 读取结果回调，直接证明原版采用战争对象标记区分事件链。

本机创意工坊模组 [More Societies: Infinity](https://steamcommunity.com/workshop/filedetails/?id=2280945168) 的 `descriptor.mod` 声明支持 `v4.5.*`。其 `events/ethic_rebuild_red_origin.txt` 在 `declare_war` 的战争效果中写 `set_war_flag = 819_war`，`common/on_actions/事件触发器.txt` 将 `red_origin.8194`、`.8195` 接入 `on_war_won`、`on_war_lost`，结果事件用 `fromfrom = { has_war_flag = 819_war }` 匹配战争。代码依据是本机已安装副本 `F:/steam/steamapps/workshop/content/281990/2280945168/`，网页仅用于标识模组。它是由模组主动发起的战争，不能证明任意原版宣战都执行同一路径；可借鉴的是“战争对象标记＋结果回调”，不是制造战争。

本机 [Gigastructural Engineering & More (4.5)](https://github.com/TheCreepOfWar/gigastructures) 在 `events/giga_012_katzen.txt` 给自己发起的干预战争写 `katzen_flusiokrieg_intervention` 战争标记，`events/giga_016_flavor.txt` 再以 `any_war`／`every_war` 查找该标记；代码依据是本机已安装副本 `F:/steam/steamapps/workshop/content/281990/1121692237/`。它说明同一国家同时参与多场战争时，应查战争实例，而不能只查国家的笼统“正在交战”状态；其 `end_war_effect` 是该模组主动控制自建战争的剧情效果，不适用于本包旁观原版战争的目标。

[Historian 作者 README](https://github.com/Kaiwen-Zhu/Historian#%E5%B7%B2%E7%9F%A5%E9%97%AE%E9%A2%98)说明它以 `on_war_beginning` 记录开始，以 `on_war_won`、`on_status_quo`、`on_status_quo_forced` 记录结束；同时明确某些特殊战争可能漏掉开始或结束回调，包括巨像全面战争中一方灭国的情况。该项目声明面向 3.8，缺口只能作为 4.5.1 测试风险，不能直接断言当前版本必然复现。

## 对 AWP-03 的处理

现有 `aemusa_ms.610` 在原版开战回调中确认觉醒失落帝国为原始攻击领袖、玩家为原始防守领袖，并给本次战争打标；`.620`～`.622` 在同一战争标记的胜、败、维持现状回调中分别写结果。这个结构与原版 `nomads` 及同类模组相符。当前不改 `.txt` 战争脚本，也不增加自定义战争目标、主动宣战、强制和平或以敌国消失推断胜利。

如果战争已记录开始，但当前战争对象不可见且没有结果回调，现有只读诊断只输出 `AEMUSA-MS|CHECK|awp_03_started_war_not_active`；第五、六章继续等待，不把“没有战争”转换为“胜利”。这属于未确认结果，不应标成失败或通过。只有真实 `on_war_won` 在带标记的同一战争上以玩家为胜方领袖触发，才获得第六章资格。

## 后续运行证明

先在隔离档观察一场合格的原版觉醒失落帝国攻击战争：保留开战前、战争中、结果后存档，核对 `qualified_fe_war_started`、战争标记、`qualified_fe_war_player_victory` 与第五六章窗口。另用玩家主动进攻、盟友参战、并发其他战争、战败和维持现状作反例。若采用脚本制造战争，只能证明引擎回调与作用域，不替代正常游玩的 FEA-01～03 证据。遇到全面战争等特殊结局无回调时，记录 `CHECK`、游戏内战争结果和存档，再决定是否需要新的事实接口；在证明之前不放宽胜利门禁。

# 晨曦舰船减伤与复活实现参考

2026-10-31。按用户要求查阅本机《晨曦：宇宙之忆》的减伤与复活源码，并对照本机原版脚本、导出的效果文档及本项目旗舰实现。本轮只补参考记录，没有修改游戏脚本、启动游戏或扩展测试。

## 来源与结论

- [作者工坊页面](https://steamcommunity.com/sharedfiles/filedetails/?id=2955341502)，本机目录为 `F:\steam\steamapps\workshop\content\281990\2955341502`。
- [本机描述文件](/F:/steam/steamapps/workshop/content/281990/2955341502/descriptor.mod:14)的名称为“晨曦：宇宙之忆”，版本字段为 `wdae`，兼容声明为 `v*.*.*`。这是本机副本声明，不证明所有游戏版本兼容，也不保证与线上最新包一致。
- 核心实现有三项：**原生比例／固定减伤、失能后恢复原舰、被摧毁后按原设计新建舰船**。它们分别负责不同能力，不能把所有“复活”说明归为同一种机制。

## 1. 减伤：直接使用原生字段

| 代表对象 | 实际写法 | 可以借鉴的部分 |
| --- | --- | --- |
| 星列标准／审判／裁决单元 | 舰体 `ship_modifier` 分别设置 `ship_damage_reduction_mult = 0.15 / 0.3 / 0.45` | 在舰体或装备上直接配置比例减伤，不需要定时扫描血量后补血 |
| 龙息作战电脑 | `ship_damage_reduction_mult = 0.05`，另有固定减伤 `ship_damage_reduction_add = 50` 和随舰体上限缩放的条件修正 | 比例减伤和固定减伤可以分开设计；先明确用途，再定数值 |
| T1能源核心 | `triggered_ship_modifier` 中设 `ship_damage_reduction_add = 0.01`，以 `mult = trigger:has_max_hp` 缩放，并排除部分本包舰种 | 固定减伤额度可以随舰体上限变化；此处不是“受到的所有伤害再减1%” |

源码入口：[标准单元](/F:/steam/steamapps/workshop/content/281990/2955341502/common/ship_sizes/常规舰船.txt:448)、[审判单元](/F:/steam/steamapps/workshop/content/281990/2955341502/common/ship_sizes/常规舰船.txt:539)、[裁决单元](/F:/steam/steamapps/workshop/content/281990/2955341502/common/ship_sizes/常规舰船.txt:632)、[电脑减伤](/F:/steam/steamapps/workshop/content/281990/2955341502/common/component_templates/常规武器.txt:993)、[能源核心](/F:/steam/steamapps/workshop/content/281990/2955341502/common/component_templates/常规武器.txt:1874)。

这两个减伤字段也存在于本机原版的[防御平台修正](/F:/steam/steamapps/common/Stellaris/common/static_modifiers/30_static_modifiers_defense_platforms.txt:2)和[圣武士特质](/F:/steam/steamapps/common/Stellaris/common/traits/18_nomads_leader_traits.txt:1)，不是该Mod自造名称。舰体文件中的 `touhou_*`、`ag_*` 则是另行出现的外部机制接口，不能与原生减伤混为一谈或直接搬入本项目。

本轮没有测定引擎减伤叠加顺序、上限或与脚本伤害的关系，不承诺“独立乘区”或“任何攻击都无效”。该包部分高阶舰写了 `ship_damage_reduction_mult = 80` 等极端值；不能把原始值80读成80%，也不把它当作本项目平衡基准。

## 2. 科罗迪亚之钥：保留原舰的失能恢复

这一支的接线完整且短：

1. [舰体定义](/F:/steam/steamapps/workshop/content/281990/2955341502/common/ship_sizes/常规舰船.txt:1112)启用 `can_disable = yes`、`stay_disabled = yes`，并设 `never_lost = yes`。
2. [巨构完成时创建舰船](/F:/steam/steamapps/workshop/content/281990/2955341502/common/megastructures/CVB_megastructures.txt:635)，在新舰上设置 `set_disable_at_health = 0.01` 和专用身份标记。按本机引擎文档，这表示到达1%舰体耐久阈值时失能。
3. [失能回调](/F:/steam/steamapps/workshop/content/281990/2955341502/common/on_actions/CVB_action.txt:4)触发 `The_Key_of_Korodia_Ark.001`。
4. [恢复事件](/F:/steam/steamapps/workshop/content/281990/2955341502/events/科罗迪亚之钥方舟机制.txt:3)核对身份标记，执行 `repair_ship = yes` 和 `set_disabled = no`，保留原对象；该事件没有次数计数、付款或延迟。

这是“失能→修复舰体→重新启用”，没有在恢复事件里新造第二艘。`repair_ship` 的本机引擎文档只承诺恢复全部舰体耐久，不能据此写成护盾、装甲也全部回满。这条接线支持其无限恢复的设计意图，但本轮未运行它，也不宣称能抵抗直接删除或一切外部脚本效果。

相关原生依据：[on_ship_disabled](/F:/steam/steamapps/common/Stellaris/common/on_actions/00_on_actions.txt:2038)、[原版失能阈值实例](/F:/steam/steamapps/common/Stellaris/events/defense_platform_policy_events.txt:19)。本机导出文档另确认 `set_disable_at_health` 接受0～1或 `no`，`set_disabled` 与 `repair_ship` 操作舰船；临时机制撤销阈值时应按原生文档使用 `no`，不照抄外部脚本中的 `-1`。

## 3. 原子重组：舰毁后按旧设计补造

- [原子分裂A槽部件](/F:/steam/steamapps/workshop/content/281990/2955341502/common/component_templates/常规武器.txt:3997)的键为 `Atomic_fission`。
- [on_ship_destroyed_victim](/F:/steam/steamapps/workshop/content/281990/2955341502/common/on_actions/CVB_action.txt:55)调用 `CVB_Korodia.27`；受害国为本事件作用域，被毁舰为 `fromfrom`。
- [原子重组事件](/F:/steam/steamapps/workshop/content/281990/2955341502/events/CVB_Korodia.txt:774)检查被毁舰带有该部件，再进入其舰队调用 `create_ship`，以被毁舰作为 `design` 和 `graphical_culture` 的来源。

这一支创建新对象，未显式迁移原舰经验、全部旗标或剧情引用；也没有在该事件内支付、计数或等待。最后一艘舰被毁时舰队作用域是否仍可用，本轮没有运行结论。可借鉴“按被毁舰设计重建”的思路，但我们现有国家级唯一记录不能省略，也不能把新对象描述为完整保留了原舰所有状态。

## 4. 有用但不能只按说明文字采用的旁支

- **临时铁幕。** [按钮效果](/F:/steam/steamapps/workshop/content/281990/2955341502/common/button_effects/重磁指针.txt:478)给舰队120日保护状态和365日冷却，为各舰设置失能阈值，并安排120日后的 `.25` 恢复、撤销阈值。这是“限时保全＋延迟恢复”的参考。[`.26` 群体恢复事件](/F:/steam/steamapps/workshop/content/281990/2955341502/events/CVB_Korodia.txt:748)虽存在，本轮在 `common`／`events` 中未找到其调用；不据此认定所有描述能力已经接通。
- **勿忘号的有友舰存活条件。** [事件注释](/F:/steam/steamapps/workshop/content/281990/2955341502/events/超级星舰机制.txt:46)写“范围内有我方舰队”，实际条件却在 `solar_system` 内检查拥有者与 `has_hp`，没有遍历另一艘友舰；本机文档中的 `has_hp` 只支持舰船作用域。修复与解除失能还放在两个独立判断中。不能直接把这一段当作已可靠实现“友舰在场才不死”的样板。

上述仅记录实际接线和可见差异，不修复第三方Mod，不为这些旁支追加测试。

## 对本项目的采用建议

1. **减伤能力优先用原生字段。** 后续D13／E10或专属舰需要这类能力时，在相应舰体、组件或有限持续修正中落地，减少战斗轮询。固定减伤与比例减伤分别定用途，数值结合我们的普通舰队、Boss和成长，不直接沿用晨曦的高数值。
2. **当前现实恒定旗舰继续保留已有恢复方式。** [现有实现](../../mod/common/scripted_effects/aemusa_ms_flagship_effects.txt:4)是国家级恢复记录、唯一实例核对和有效首都重建；基础90日，爱缪莎等级11／21后分别75／60日。已有[90日受控缺失恢复记录](../../reports/aemusa_main_story_milestone_1_2026-10-07.md:132)可复用；该记录明确没有证明战斗摧毁回调已实测，不扩大证据范围。
3. **原舰失能恢复作为明确备用方案。** 若后续需要保留同一实体或现有重建确有问题，可用已获准的失能方案，并保留冷却和现场支撑中断；不因看到即时恢复实例就改变已确定的战败代价。本轮没有更换恢复路径或承诺全面迁移自定义设计。
4. **普通公共舰与个人唯一舰分开。** 此次参考不把公共科技改成全舰无限复活，也不把个人能力并入文明公共树。正式设定及名称仍按七都数据库的来源规范处理。
5. **验证保持集中。** 本轮只核对文档差异与引用。以后实际改动哪一种能力，就在阶段试玩中观察一次对应的受伤／恢复和唯一性；不重测所有旧章节、不穷举外部Mod组合。

本记录补充[大型物种文明包参考](artifact_species_pack_mod_reference_2026-10-31.md)。它是源码参考入口，未改变当前D13接手点，也不是新的游戏测试队列。

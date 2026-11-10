# 六 L 旗舰旧档的设计绑定

## 存档证据

以下为本国（ID 0）的真实舰船与已序列化设计，各档均只有一艘该舰种。逐槽比对了船上实装武器和设计内容。

| 存档 | 游戏版本 | 舰船 ID | 舰队 ID | 原名全局设计 ID | 舰艏／中段／舰尾 |
| --- | --- | ---: | ---: | ---: | --- |
| `2293.10.11-r3e-reserve.sav` | 4.5.2 | 16777294 | 16777259 | 67108880 | 2L／3L／1L |
| `2293.12.03.sav` | 4.5.3 | 16777294 | 16777259 | 67108880 | 2L／3L／1L |
| `2200.01.01-prebattle.sav`（新局对照） | 4.5.3 | 1641 | 215 | 1505 | 12T／0T／4T |

三个存档都把 `NAME_Aemusa_Reality_Flagship` 用作全局设计名。4.5.3 已重新保存的旧档仍通过该名找到设计 67108880，舰上是三门大型伽马激光和三门大型高斯炮。新局同名设计 1505 装载十六门恒定主炮。

## 正式创建

首次授舰与手动召回共用建舰效果，从独立键 `NAME_Aemusa_Reality_Flagship_16T` 创建设计，随即将 `last_created_design` 交给该舰。舰名继续显示「未闭合的航路」。六 L 旧舰继续引用存档中的设计与区段。新旧舰共用 5% 船体瘫痪保护，原生 `on_ship_disabled` 在原船上执行 `repair_ship` 和 `set_disabled = no`。脚本彻底删除舰体后，由玩家在「联络爱缪莎」召回；旧冷却事件仅清理旧票据。

本机 4.5.3 原版在 `events/anomaly_events_2.txt` 的 R44 事件以及 `common/scripted_effects/archaeology_event_effects.txt` 的 Grand Herald 创建效果中使用同一对引擎操作。专项预检从本 Mod 的正式入口追踪到新设计，得到舰艏 12T、舰尾 4T，供能余量 1,470。

## 运行验证

11 月 10 日，本机《群星》4.5.3 载入上表 `2293.12.03.sav` 的独立副本。2293.12.04，测试脚本在原六 L 旗舰上执行 `set_disabled = yes`。游戏同日在原生瘫痪回调中运行正式修复效果。随后读取到同一艘船、同一支舰队、同一星系，舰船已能行动，船体至少 99%，本国仍只有一艘该舰种。三条记录的现实时间均为 22:07:06。

```text
AEF16|DISABLE|begin_scripted_disable
AEMUSA-MS|AWP-06|flagship_revived_in_place
AEF16|DISABLE|same_ship_fleet_system_operational
```

另一项测试在该副本中用脚本实际删除舰船。2293.12.06，月检和原冷却回调执行后，舰位仍空。夹具连续两次调用与爱缪莎联络按钮共用的正式召回效果，游戏只记录了一次造舰。验收读取到恰好一艘该舰种，带专属反应堆与恒定主炮，再次召回的条件已关闭。

```text
AEF16|RECALL|absent_before_manual_contact
AEMUSA-MS|AWP-06|flagship_created
AEF16|RECALL|one_new_T_design_after_manual_contact
```

本例验证了脚本致瘫以后的同舰即时复活，以及真实删除以后的召回效果。自然交火击穿 5% 船体线和手动点击联络按钮分别保留为独立观察项。新设计的逐槽配置见上节预检，这次召回在游戏内检查了舰船数量、反应堆与主炮的存在性。原始记录位于本机 `temp/late_game_2293_20261110/profile/logs/game.log`。[测试入口与核对方式](../tools/validation/runtime_fixtures/aef16_live_fire/README.md#瘫痪与真正删除)

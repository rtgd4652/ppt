# 大型物种与文明包的实现参考

2026-10-31。用户要求进一步查看大型物种包。本轮只读本机舰R、久远之旅、群星争霸的代表源码，重点对照文明资格、公共研究、建筑与舰船接入；没有修改游戏脚本、复制第三方资产或运行游戏测试。现有代码保存点仍为`1a90c09`，之前工程参考文档提交为`b57b6d4`。

## 范围与版本

| 本机Mod | Workshop ID | 描述文件中的兼容声明 | 本轮重点 |
| --- | --- | --- | --- |
| Warship Girls R And MIST Species（舰R） | `1747099270` | `v4.5.*`，版本字段`0.1` | 政体资格、特色研究与生产设施、可设计大舰的船厂入口 |
| Voyage to Eternity（久远之旅） | `2766998502` | `v4.4.6` | 物种、剧情国家、技术和舰船许可分层；原生法令承担持续工程能力 |
| 群星争霸 StellarisCraft | `2677473144` | `v4.5.2` | 政体／起源／国策分支，研究与建筑／舰体的明确对应，外观与玩法条件分开 |

版本信息来自本机`descriptor.mod`，不代表线上最新版或本项目兼容性已验。也查看了星之誓约几个描述文件，但没有把其补丁、测试版当作独立文明包进行本轮分析。

## 已读实例

### 舰R：把文明研究接到原生生产和造船

- `has_wg_authority`集中识别舰娘／深海政体。`tech_senergy_dreadnought`使用这个条件和既有空间压缩科技限定资格。见[政体判断](/F:/steam/steamapps/workshop/content/281990/1747099270/common/scripted_triggers/19_wsg_scripted_triggers.txt:21)、[大舰研究](/F:/steam/steamapps/workshop/content/281990/1747099270/common/technology/wsg_sep_tech.txt:1616)。
- `tech_wsg_senergy`对应生产设施。`building_wsg_senergy_1`读取该研究，提供岗位、维护与升级入口，部分产出由传统标记影响；文明研究由实际生产环节承接。见[设施定义](/F:/steam/steamapps/workshop/content/281990/1747099270/common/buildings/16_wsg_project_s_buildings.txt:475)。
- `dreadnought_carrier`设为可设计、读取研究前置，使用`starbase_shipyard`建造，并单独核对船厂场所和设施；同文件另有不可设计的特殊舰。两类对象并不共用一套取得方式。见[舰体定义](/F:/steam/steamapps/workshop/content/281990/1747099270/common/ship_sizes/10_wsg_dreadnought.txt:85)。

对我们的启发：公共舰用科技应连接真实可装配组件／建造入口，角色唯一舰继续使用自己的身份与剧情路径。借鉴职责连接，数值、特色资源、来源设定和资产仍按本项目设计；不把这份源码中的高数值直接作为平衡基准。

### 久远之旅：物种身份、故事国家与内容许可分别判断

- 物种判断在`KZ_VOY_species_triggers`中使用物种原型或特质；故事国家判断则读取登记的国家目标，另分起源线、非起源线及继承后的资格。见[物种判断](/F:/steam/steamapps/workshop/content/281990/2766998502/common/scripted_triggers/KZ_VOY_species_triggers.txt:115)、[剧情授权](/F:/steam/steamapps/workshop/content/281990/2766998502/common/scripted_triggers/KZ_VOY_authorization_triggers.txt:34)。
- 舰船科技统一调用`KZ_VOY_NGAS_potential`，根据类型与设置决定开放范围；造船场所又由独立条件核对。见[舰船许可](/F:/steam/steamapps/workshop/content/281990/2766998502/common/scripted_triggers/KZ_VOY_ship_NGAS_triggers.txt:1112)、[科技调用实例](/F:/steam/steamapps/workshop/content/281990/2766998502/common/technology/03_KZ_VOY_NGAS_tech.txt:4)。这说明共用判断可以减少各处重复条件，并不意味着我们要复制它的全部配置模式。
- “零重力建造”以原生长期法令承接研究、资源开支、维护、建造速度和+1巨构建造上限；立绘／舰船设置则用一次性法令打开专门入口。见[法令实例](/F:/steam/steamapps/workshop/content/281990/2766998502/common/edicts/!!!!!!!!_KZ_VOY_edicts.txt:7)。许多文明能力可以放在原生界面，不必另造一串事件。

对我们的启发：继续区分神器文明公共能力、主线参与资格、爱缪莎个人转变与唯一对象身份。复用本项目已有接口；新内容明确属于哪层，已通过的主线和64项公共科技不因本次参考被整体重写。容量法令只是另一种实现参考，E09本轮不改成新法令。

### 群星争霸：用具体制度和设施条件形成文明分支

- 物种定义负责特质与`graphical_culture`；国家级科技根据政体、起源、国策或传统分别开放。见[物种与外观映射](/F:/steam/steamapps/workshop/content/281990/2677473144/common/species_classes/StellarisCraft_species_class.txt:3)、[研究分支](/F:/steam/steamapps/workshop/content/281990/2677473144/common/technology/SC_daelaam_technologies.txt:15)。外观选择与某项玩法的开放条件各自有定义。
- 光影议会建筑要求对应研究与政体，还要求当地水晶塔修正，再提供特定岗位。见[建筑定义](/F:/steam/steamapps/workshop/content/281990/2677473144/common/buildings/SC_daelaam_buildings.txt:59)。文明特色落实到“在什么条件下能建设、建设后能做什么”。
- 风暴战舰研究读取传统及动力／航行／传感／电脑技术条件；舰体读取研究和起源，并接原生船厂及必需组件集合。见[舰船研究](/F:/steam/steamapps/workshop/content/281990/2677473144/common/technology/SC_daelaam_technologies.txt:123)、[舰体入口](/F:/steam/steamapps/workshop/content/281990/2677473144/common/ship_sizes/SC_daelaam_ship_sizes.txt:2)。这是研究与实物能力衔接的例子，本轮未验证其实际配装和平衡。

对我们的启发：神器文明应在经济、设施与军备中持续体现特色；条件要服务于具体玩法。既有B14备料、E09营建及后续舰用能力可以形成衔接，但不要为每项普通研究额外增加仪式、支付窗口或新的全局账本。

## 接入现有计划

1. **D13和E10按原责任表分工。** D13负责高阶承载与公共特殊舰体基础，能源／推进／FTL变体仍分别结合D16／D17／D18；E10承接公共战略舰体工程。角色唯一旗舰与个人终局舰保持独立，不能拿旧专属核心替代公共装备。
2. **研究优先交付实际能力。** 新节点明确对应组件、舰体、设施、工程或现有系统中的功能；数量目标不应变成只增加一行科技名称。
3. **特色集中到可持续使用的系统。** 普通建造、升级、维护与岗位优先使用原生机制；剧情窗口服务选择、角色表现和重要结果。新资源须先有明确用途和生产消费关系，不因参考包资源多就照搬。
4. **来源职责清楚。** 这些Mod提供技术组织方式；七都数据库及其指向的正式来源继续决定术语和设定。人物组合、正式美术定稿和连续巨构原型仍按用户原有约定，不因参考恢复。
5. **保持轻量验证。** 本轮只做文档引用和差异检查；不新增测试或载档。后续只检查新改动的核心风险，原生流程取代表路径，沿用已有证据，不穷举这些外部包或追求全面兼容。

本记录是后续按需查阅的入口，不是待执行测试队列。大型工程的原生阶段链另见[工程参考](artifact_large_engineering_mod_reference_2026-10-31.md)，D13／E10分工见[完整路线](artifact_civilization_research_building_route_v0.3.md)及[军备责任表](artifact_civilization_military_research_plan_v0.1.md)。

用户随后指定的晨曦舰船机制已单列[减伤与复活参考](artifact_dawn_ship_survival_mod_reference_2026-10-31.md)：已读比例／固定减伤、原舰失能修复、舰毁后按旧设计补造及对应回调，并核对本机原生字段。保留本项目现有冷却与唯一记录，本次只补参考，未改游戏脚本或运行测试。

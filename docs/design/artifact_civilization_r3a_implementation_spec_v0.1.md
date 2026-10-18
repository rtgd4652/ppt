# R3a 舰载基础与测距实施规格

2026-10-18，基线`3e980fe`。状态：规格及源码已接入，静态与定向引用检查通过，游戏待验，见[实施记录](../../reports/artifact_civilization_r3a_implementation_2026-10-18.md)。继续[公共路线v0.3](artifact_civilization_research_building_route_v0.3.md)与[军备责任表](artifact_civilization_military_research_plan_v0.1.md)，只接D04／D05／D15；研发不读取人物组合、爱缪莎转变或最终Boss结算。设计数值为首版参数，不作为新增原作事实或平衡结论。

## 交付能力

舰载接口提供一枚占用A槽的固定供能适配器，为功率紧张的小型舰提供另一种配装选择；相位测距提供远距观测与近距射控两种传感器；符文装甲用部分装甲量、额外造价和维护换取更高装甲硬化。三项研究均交付实际装备，不额外叠加全国数值。

合计3项公共研究、6个组件定义（1枚A槽、2种传感器、同一装甲族S／M／L三尺寸）及2个新组件集合。传感器沿用原生`sensor_components`必需槽集合，不另设核心槽。当前已为41项公共科技、60个组件定义（旧54＋本包6），不代表游戏和整体平衡已验。现有29个行星建筑及1个星港建筑不在本包变化范围。

## 研究卡

| 节点／新键 | 分类 | 前置 | 科研费／权重 | 解锁 |
| --- | --- | --- | --- | --- |
| D04 神器舰载接口，`tech_artifact_shipboard_interface` | 工程T2／voidcraft | D01 `tech_artifact_user_combat_doctrine`＋B06 `tech_artifact_standard_parts` | 1600／110 | 标准化供能适配器 |
| D05 相位测距阵列，`tech_artifact_phase_ranging_array` | 物理T3／computing | D04＋A06 `tech_artifact_long_baseline_measurement` | 3600／90 | 观测型、射控型相位测距仪 |
| D15 符文舰体装甲，`tech_artifact_runic_hull_armor` | 工程T3／materials | D04＋B07 `tech_artifact_resonance_material_screening` | 3600／90 | 一族三尺寸符文舰体装甲 |

三个科技均使用公共`ARTIFACT_USER`主体物种资格，保留原图已定前置。不把旧军备总包当作新研究自动完成，也不批量赠送新科技。D09尚未实施，本包不预先生成复合装甲；后续新复合变体仍要求D15＋D09。

## 装备卡

| 新组件键／类型 | 首版性能 | 费用与月维护 | 取舍 |
| --- | --- | --- | --- |
| `ARTIFACT_STANDARD_POWER_ADAPTER`，A槽 | `power = 30`，提供固定30功率；自身无额外修正 | 12合金；0.20能源／0.02合金 | 占用A槽；不按反应堆百分比增长，大舰与高阶反应堆仍需其他供能方案 |
| `ARTIFACT_PHASE_OBSERVATION_SENSOR`，medium传感器 | 功耗25；`sensor_range = 4`、`hyperlane_range = 6`、追踪加值5 | 15合金；0.15能源 | 航道探知优先，射控较低 |
| `ARTIFACT_PHASE_FIRE_CONTROL_SENSOR`，medium传感器 | 功耗20；`sensor_range = 2`、`hyperlane_range = 3`、追踪加值20 | 15合金；0.15能源 | 近距射控优先，降低远距观测；限军用舰级 |
| `SMALL_ARTIFACT_RUNIC_HULL_ARMOR`，small防御槽 | 功耗0；装甲140；装甲硬化加值0.08 | 18合金；0.18能源／0.035合金 | 较同代原版装甲降低厚度，换取抗穿透 |
| `MEDIUM_ARTIFACT_RUNIC_HULL_ARMOR`，medium防御槽 | 功耗0；装甲420；装甲硬化加值0.08 | 45合金；0.35能源／0.070合金 | 同族尺寸，不另计科技 |
| `LARGE_ARTIFACT_RUNIC_HULL_ARMOR`，large防御槽 | 功耗0；装甲1260；装甲硬化加值0.08 | 112合金；0.70能源／0.140合金 | 同族尺寸，不另计科技 |

上述资源均走原生`ship_components`经济，接受游戏实际修正。固定供能使用通用utility的正`power`字段，不写臆造的功率修正；需要在本包唯一代表配装中实际确认A槽增加30可用功率。多A槽按原生槽位规则工作，每枚仍占一槽；没有额外全帝国唯一标记或免费舰队效果。

传感器范围写直接字段；追踪分别用`ship_modifier.ship_tracking_add`的5与20，表示加值，不能写成百分比。两种传感器占同一个原生传感器槽，互相排斥，不建立彼此`upgrades_to`，也不接入旧`ARTIFACT_SENSOR_1→2→3`链。航道探知不等于隐形探测、情报解密或无视星云，舰队感知仍由原生规则处理。本包不修改A06地表阵列、E06星港接口或国家传感器加成。

装甲值写入`modifier.ship_armor_add`；硬化写入`ship_modifier.ship_armor_hardening_add`。0.08是原生相加修正，不承诺最终伤害降低8%，也不代表绕过装甲克制。尺寸间装甲按1:3:9，硬化按原版逐组件规则相加，最终上下限交给游戏。所有新件均无舰体再生、复活、作战电脑行为或光环。

## 槽位、身份和自动设计

所有新件以ship作用域的`from`读取拥有国的公共身份，并要求`country_uses_bio_ships = no`，本包只服务常规机械船体的现有兼容槽。A槽和装甲以实际槽位决定适用舰体；观测型可用于具有原生传感器槽的机械军民船，射控型另要求`shipclass_military`。不覆盖生物舰／太空生物组件集合，也不为特殊舰强塞新槽。

新集合仅为`ARTIFACT_STANDARD_POWER_ADAPTER`与`ARTIFACT_RUNIC_HULL_ARMOR`，均不加`required_component_set`或`is_core_component_set`。传感器使用已存在的`sensor_components`，原版无科技基础传感器保持，以免临时设计国家或未研究D05的旧设计失去必需槽候选。

不修改原版／旧Mod件的自动升级指针。新件先采用保守AI权重（A槽3、观测10、射控12、装甲12）；不承诺自动最佳设计会选择它们，也不自动把玩家手动选择的两种传感器互换。验收使用手动设计与正常改装，具体自动设计策略留待全军备平衡。

## 旧内容衔接

现有三个总包、43个旧公共组件、7个命运之主限定件、4个光环原型及3类旧陆军均保留原键、原前置、原升级链和数值。新科技与新件全部使用独立键，不重命名旧设计，不重写已造舰船，不免费替换舰上装备。旧中后期传感器的5／6、9／9等数值可能优于本包新分工件，这是遗留平衡边界，不能通过悄悄削弱旧件解决。

本包不迁移旧总包，也不声称新增分支后旧包已收敛。后续完整军备路线接齐后，再单独设计新旧档迁移与平衡。公共供能辅助件不复用命运之主50000功率反应堆；个人专属研究与最终Boss奖励继续独立。

## 实现顺序与文件

只创建下列Mod文件，名称在实际写入前仍需碰撞核对：

- `mod/common/technology/artifact_shipboard_foundation_technology.txt`
- `mod/common/component_sets/artifact_shipboard_foundation_sets.txt`
- `mod/common/component_templates/artifact_shipboard_foundation_components.txt`
- `mod/localisation/simp_chinese/artifact_shipboard_foundation_l_simp_chinese.yml`

按技能每批不超过三种对象类型：先写科技、集合、本地化，再接六个utility组件并补说明；两批连续完成后才算功能交付。科技、集合、组件为UTF-8无BOM，本地化为UTF-8 BOM。现有源文件不做格式重写。

使用已存在的`tech_artifact_user_combat_doctrine`、`tech_artifact_black_gate_observation`、`tech_artifact_relic_fabrication`科技图标，组件用`GFX_ship_part_reactor_booster_1`与既有神器传感器／命运装甲图标占位。全部仍待后续绘图工具统一重构，不新增本包美术或模型。

## 一轮验证

源码检查只核对前置与集合引用、身份／船型作用域、直接范围与修正字段，以及旧54组件的语义未改；静态检查沿用项目脚本。装备参数来自本机4.5.2，不能把尚未运行的规格当作4.5.1兼容证明。

游戏只安排一次冷启动，以当前已保留的R2f启用态为测试分支：按需受控补研究，记录来源；在一艘普通护卫舰的手动设计中核对本舰四个适用候选（A槽、两种传感器和small装甲），选固定供能适配器、射控型测距仪和small符文装甲，确认功率、槽位及提示，再通过正常船厂改装。只保留一处改装完成后的检查点，实际载回一次，核对设计和实舰仍使用新件。已有三尺寸的静态映射复用，不为每尺寸另造舰；不生成敌军或为本包安排战争回放。装配和面板通过不冒称战斗收益、银河地图感知或自然经济平衡已验。

## 本机依据

- `common/component_templates/00_utilities_aux.txt`：原生A槽与反应堆增压器写法；原版按20%／33%／50%提供百分比供能，新件选固定功率表达另一种用途。
- `common/component_templates/00_utilities_sensors.txt`：传感器medium、范围直接字段、追踪ship_modifier；原版SENSOR_3为3／4、追踪10、功耗15、6合金。
- `common/component_templates/00_utilities.txt`与`common/scripted_variables/02_scripted_variables_component_cost.txt`：原版T3装甲160／480／1440、硬化0.02；费用12／30／75，作为厚度和硬化取舍的比较基线。
- `common/component_sets/00_required_sets.txt`、原生辅助／装甲集合和`common/ship_sizes/00_ship_sizes.txt`：必需传感器集合、军用船级和槽位职责。
- [旧组件](../../mod/common/component_templates/aemusa_artifact_components.txt)、[旧分阶段组件](../../mod/common/component_templates/aemusa_artifact_tiered_components.txt)、[既有科技](../../mod/common/technology/aemusa_technology.txt)及R1／R2公共研究：保留边界与真实前置。

[结构化规格](artifact_civilization_r3a_implementation_spec_v0.1.json) · [本轮记录](../../reports/artifact_civilization_r3a_spec_2026-10-18.md)

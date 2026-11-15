# P03命运舰体接口：择途级独立舰体

2026年11月15日，用户恢复P03并选择“另做专属舰体”。现已实现独立舰种 `aemusa_fate_escort`（择途级）：可以在设计器配装，从正常船坞付费建造、维护和改装。它不替代“未闭合的航路”，也不进入唯一旗舰的创建、复原、召回或主线节点识别流程。本包源码检查通过，原生设计器、造舰、改装、读档和战斗仍待阶段试玩。

## 研究与建造

P03为工程学五阶、18,000研究费用、100抽取权重，前置P01。研究资格直接调用已有 `aemusa_personal_research_eligible`：正式授权、自主接受、合法转变和第十六章收束记录必须同时成立；等级、旧飞升或遗留研究不提供替代入口。研究不创建免费舰船，也不修改主线事实。

新建订单还要求公共中庭级研究与本国承载定型、运行中的分段营建场，以及擎天堡船厂或完工/修复巨型船坞。公共条件只被P03单向读取，公共科技与舰体没有新增个人门槛。工业停运、占领、轰炸或拆除会挡住新订单，但不从现有设计移走五类专用核心；个人历史与P03知识仍需成立。

## 首版参数与构型

| 项目 | 择途级首版 |
| --- | --- |
| 定位 | 个人路线的重型炮击舰；舰员执行航行与战斗，正常承担战损 |
| 舰体 | 12,000船体，60容量，基础建造1,080天 |
| 基础构型 | 6L武器、8L防护、2A；未掌握X武器也可完整配装 |
| 主炮构型 | 1X+4L武器、7L防护、2A；舰首沿用4.5.4原版X武器OR研究列表，不赠送任何主炮研究 |
| 舰体与三段价格 | 基础构型4,800合金，主炮构型5,000合金；实际武器、防护和核心另计 |
| 舰体维护 | 每月15能源、7.5合金，另计实际组件；物流12 |
| 必需核心 | 独立反应堆、推进器、超空间航道引擎、传感器、炮击电脑，共五类 |
| 专属电脑 | 本舰射速+15%、射程+25%、追踪+5；使用原生炮击行为，无保证命中或直接改写战果 |
| 复原与数量 | 正常损失后付费重建，无复活回调；按正常容量、资源与船坞队列约束，不添加未核实的额外数量上限 |

容量采用当前中庭级60作为基准。中庭级为9,600船体、基础三段构型3,600合金；其传承X舰首构型4,000合金。择途级以更高船体、机动与专用电脑换取额外造价和维护，仍只有普通L/X武备。唯一16T旗舰的特殊容量与复原属于已有叙事机制，不能按其特殊实参倒推可量产舰体的定价。本次不改旗舰数值，择途级首版成本与作战收益尚未经过平衡试玩。

原版必需核心助手存在舰种白名单，因此本包独立定义五类核心，明确限定择途级。使用现有 `power_core`、`ftl_components`、`thruster_components`、`sensor_components`、`combat_computers` 集合，不改公共或旗舰白名单。航道引擎沿用原生高级超空间效果，没有新增跳跃或瞬移；组件总造价1,050合金，反应堆3,200功率，其他四类核心合计消耗395功率，余量由实际武备和防护占用。

## 来源与表现

写前只读查询本地七都SQLite的 `TERM-ARTIFACT`、`TERM-ARTIFACT-WIELDER`、`TERM-ARTIFACT-SCIENCE`、`TERM-FATE-RULES`，随后读取其指向的神器体系、命运规则工作定义及爱缪莎角色资料。神器/神器使原作术语仍为 `under_review`，神器科学/命运规则为项目定义，审核状态没有改变。择途级的名字、技术、舰体和参数属于Mod设计，来源只约束人物、可能性、现实代价与文明协作的表达。P03卡面和实际消费者已登记到[文案目录](../docs/design/artifact_technology_text_catalog_v0.1.json)。

**没有新增独立舰模。** 当前根实体及标准舰首、主炮舰首、炮击中段、舰尾分别复用已存在的 `ccv04_strategic_cruiser_entity` 与四个 `ccv04_runtime_*` 实体，仅作为新舰种代码的表现占位。原定位器和武器挂点沿用，不重画或替换唯一旗舰。科技与部件图标也复用已有资源。择途级具体外观尚待设计，不能把本包称为美术定稿。

## 检查与下一步

6项新增检查读取正式脚本并回放真实终章账本，覆盖P01/正式转变/收束资格、两种拒绝、公共工业失效、船坞阶段、核心舰种与国家历史隔离，以及无X研究时仍可完整设计的基础构型。10项原P01及中庭级检查通过。4.5.4静态检查0错误、0警告；脚本无BOM，中文本地化有BOM。没有操作游戏或修改原生存档。

执行记录：在仓库根目录设置 `PYTHONPATH=tools/validation;tools/validation/tests`，运行 `python -B -m unittest test_aemusa_fate_hull -v`（6项，0.159秒，OK）及 `python -B -m unittest test_aemusa_personal_research test_artifact_strategic_hull -q`（10项，0.133秒，OK）。静态命令为 `python -B tools/validation/check_mod.py --game-dir F:\steam\steamapps\common\Stellaris --json`，覆盖298脚本、270事件、2397中文键、795登记状态及738引用状态，返回pass。输出保留于工具回执，本次未另存日志文件。

独立只读复核另回读了当前生产PDX：标准舰首2L、主炮舰首XL、中段3L、舰尾1L的定位器均存在，根实体的part1/2/3与四个目标定位器齐备，引用贴图与科技图标存在；原版普通L/XL武器没有排斥这个机械舰型。此范围是模型引用与挂点核对，不能替代新舰种实际射击和自动配装。

阶段试玩只需一个合法终章隔离档：正常取得研究、设计基础或X构型、付费下单与一次改装，并在正常续玩时核对保存；不重跑终章或逐组件存档。引擎实际队列扣费、自动设计选择、X主炮发射、工业恢复后下单及战斗平衡尚未验。本包无新持久化旗标或月度扫描，旧档得到的是新增研究与舰种定义，不改既有设计或舰船实例。

## 文件范围

- 新增：`mod/common/technology/aemusa_fate_hull_technology.txt`、`mod/common/scripted_triggers/aemusa_fate_hull_triggers.txt`。
- 新增：`mod/common/ship_sizes/aemusa_fate_escort.txt`、`mod/common/section_templates/aemusa_fate_escort_sections.txt`、`mod/common/component_templates/aemusa_fate_escort_components.txt`。
- 新增：`mod/localisation/simp_chinese/aemusa_fate_hull_l_simp_chinese.yml`、`tools/validation/tests/test_aemusa_fate_hull.py`及本报告。
- 更新P03记录：`docs/design/artifact_civilization_research_building_route_v0.3.md`、同名JSON、`docs/design/artifact_technology_text_catalog_v0.1.json`。其他P线脚本、唯一旗舰、公共造境和主线节点脚本未改。

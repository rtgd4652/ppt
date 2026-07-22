# 美术规范、参考图库与正式资产导航

> 本页是 `docs/art/` 的流程入口。它不复制参考清单，也不授予任何素材使用权；它说明“到哪里查证、由哪份文档作决定、正式资产如何登记”。

## 1. 三套文档的职责

| 层级 | 位置 | 回答的问题 | 不能替代什么 |
| --- | --- | --- | --- |
| 视觉证据层 | [`../reference_library/`](../reference_library/) | 项目看过哪些资料、来源在哪里、能学习什么、不能复制什么、权利状态如何 | 不能直接决定正式资产可发布，也不能把参考图变成项目资产 |
| 规范决策层 | [`../ART_BIBLE.md`](../ART_BIBLE.md) 及其分册 | 项目统一风格是什么，新资产应怎样设计、制作和审核 | 不能替代原作事实证据、许可审核或游戏内测试 |
| 正式资产层 | [`../ASSET_REGISTRY.csv`](../ASSET_REGISTRY.csv) | 哪个项目资产准备或已经进入生产／运行时目录，它如何创作、引用哪些规律、能否发布 | 不能反向证明参考图拥有许可，也不能用一行登记跳过审核 |

一句话流程：**参考图库提供证据，Art Bible 提炼规则，生产流程创造新资产，资产登记表记录可追溯结果。**

## 2. 推荐阅读顺序

### 新画师／概念设计人员

1. [`../ART_BIBLE.md`](../ART_BIBLE.md)：项目定位、三层视觉体系和资产规则；
2. [`../COLOR_SYSTEM.md`](../COLOR_SYSTEM.md)：颜色职责与强度；
3. [`../SHAPE_LANGUAGE.md`](../SHAPE_LANGUAGE.md)：公共、神器和个人形状层；
4. [`../MATERIAL_GUIDE.md`](../MATERIAL_GUIDE.md)：材料、磨损和发光关系；
5. 对应的 [`../characters/`](../characters/) 或 [`../ships/`](../ships/) 分册；
6. [`../ART_STYLE_ANTI_PATTERNS.md`](../ART_STYLE_ANTI_PATTERNS.md)：快速排除错误方向；
7. 本资产相关 Moodboard 和已审核 `reference_id`；
8. [`../ART_REVIEW_CHECKLIST.md`](../ART_REVIEW_CHECKLIST.md)：提交每轮审核材料。

### AI 绘图人员

1. 完成上述项目公共规范阅读；
2. 使用 [`../AI_ART_GUIDE.md`](../AI_ART_GUIDE.md) 固定公共风格段和对应变量模板；
3. 只上传权利范围允许进入相应生成服务的参考；
4. 把输出标为候选方案，不把生成结果当作原作事实；
5. 输出进入正式制作前走美术、技术、权利和资产登记流程。

### 建模、贴图和特效人员

1. 阅读 `ART_BIBLE`、形状、材质和舰船／巨构分册；
2. 从《群星》参考页只学习视距、section、定位器、LOD、材质通道和性能尺度；
3. 把实体、贴图、着色器、粒子和动画职责拆开；
4. 在 R3 制作可行性和 R4 游戏内审核阶段提交模型与性能证据；
5. 正式导出文件进入 `ASSET_REGISTRY.csv`。

## 3. 参考图库入口

### 总览与权利

- [参考图库说明](../reference_library/README.md)
- [现有资源审计](../reference_library/EXISTING_RESOURCE_AUDIT.md)
- [参考索引](../reference_library/REFERENCE_INDEX.md)
- [参考登记表](../reference_library/REFERENCE_MANIFEST.csv)
- [来源与权利规范](../reference_library/SOURCE_AND_RIGHTS.md)
- [参考层反面案例](../reference_library/ANTI_REFERENCES.md)
- [中央庭公共材质校准板](../calibration/CENTRAL_COURT_MATERIAL_CALIBRATION.md)
- [黑门与异界正式视觉对照组](../calibration/BLACK_GATE_OTHERWORLD_COMPARISON.md)

`REFERENCE_MANIFEST.csv` 中的 `review_status` 是使用优先级的重要依据：

- `approved_anchor`：可以作为主要视觉锚点，但仍需遵守其授权边界；
- `supporting`：只作为技术、材质、构图或辅助参考；
- `source_uncertain`／`unreviewed`：只能提示资料和审核缺口，不能固定原作事实；
- `rejected`：不再作为正向参考；

`planned_reference_slot` 属于 `source_type`，表示计划中的参考空位，不是可用素材，也不能代替 `review_status`。`anti_reference` 属于 `visual_role`，用于说明条目只承担反面案例作用。

### 原作参考分析

- [角色](../reference_library/original_game/CHARACTERS.md)
- [环境](../reference_library/original_game/ENVIRONMENTS.md)
- [UI 与图标](../reference_library/original_game/UI_AND_ICONS.md)
- [效果](../reference_library/original_game/EFFECTS.md)

原作参考用于确认角色识别、城市与机构气质、神器媒介、黑门及技能表现。除非有明确再分发许可，图片本体默认只保存在 Git 忽略的本地参考目录。

### 《群星》技术与视觉尺度

- [舰船](../reference_library/stellaris/SHIPS.md)
- [巨构](../reference_library/stellaris/MEGASTRUCTURES.md)
- [星球与区划](../reference_library/stellaris/PLANETS_AND_DISTRICTS.md)
- [UI 与图标](../reference_library/stellaris/UI_AND_ICONS.md)
- [粒子特效](../reference_library/stellaris/PARTICLE_EFFECTS.md)
- [考古](../reference_library/stellaris/ARCHAEOLOGY.md)
- [星界间隙](../reference_library/stellaris/ASTRAL_RIFTS.md)

《群星》参考主要回答“在游戏中怎样读得清、跑得动、接得上技术流程”，不规定本 Mod 最终阵营造型。

### 外部辅助设计

- [建筑](../reference_library/external/ARCHITECTURE.md)
- [材质](../reference_library/external/MATERIALS.md)
- [天文仪器](../reference_library/external/ASTRONOMY.md)
- [工业设计](../reference_library/external/INDUSTRIAL_DESIGN.md)

外部作品只能用于分析结构、材质、构图、色彩关系、光影和动态原理，不得复制其角色、舰船、标志、独特轮廓或标志性构图。

## 4. Moodboard 入口与用途

| Moodboard | 解决的问题 | 不解决的问题 |
| --- | --- | --- |
| [中央庭](../reference_library/moodboards/CENTRAL_COURT.md) | 公共文明的理性、秩序、重建和现代工程底层 | 不定义任何角色个人服装或神器 |
| [神器科技](../reference_library/moodboards/ARTIFACT_TECHNOLOGY.md) | 工程外框、规则接口与异常核心的结构关系 | 不规定所有神器统一颜色和图案 |
| [爱缪莎](../reference_library/moodboards/AEMUSA.md) | 星月、命运轨迹、卡牌边界及个人配色关系 | 不把爱缪莎风格扩大到全文明 |
| [安托涅瓦](../reference_library/moodboards/ANTONIVA.md) | 原作基础／觉醒识别、方舟、空间容纳与庇护方向 | 不把皮肤或觉醒状态改写成基础形态 |
| [命运之主](../reference_library/moodboards/DESTINY_SOVEREIGN.md) | 从零重设计的证据门槛、功能问题与禁止方向 | 旧 Stage 9 已退出该身份，不能继续修补后换色复用 |
| [旧世界回声](../reference_library/moodboards/OLD_WORLD_ECHOES.md) | 档案、生活遗物、记忆失真和历史痕迹 | 不把所有遗珍变成金色宝物或恐怖鬼影 |
| [异界与星界间隙](../reference_library/moodboards/OTHERWORLD_AND_ASTRAL_RIFTS.md) | 黑门、规则不兼容、空间折叠和可控异常边界 | 不复制《群星》虚境紫色或外部异界生物 |

Moodboard 是有结论的参考组，不是图片拼贴。每次引用都应写出具体 `reference_id`、要学习的抽象规律和不得复制的部分。

## 5. 从参考到正式资产

```text
登记参考来源与权利
        ↓
人工审核 reference_id
        ↓
Moodboard 提炼可学习规律与禁区
        ↓
Art Bible 形成项目统一规则
        ↓
概念草案／AI 候选／结构设计
        ↓
R0–R4 美术与游戏实现审核
        ↓
ASSET_REGISTRY.csv 正式登记
        ↓
R5 权利与发布审核
        ↓
进入 assets／mod 生产与运行时目录
```

关键门槛：

- 参考图不能通过改名、裁切、调色、描边、格式转换或 AI 重绘直接变成正式资产；
- `unknown` 不能自动升级为 `licensed`；
- `official_game_reference` 不等于项目拥有原图发布权；
- `project_created` 仍需核查输入素材、字体、纹理、模型、生成服务和发布条件；
- `supporting` 表示可辅助判断，不表示其全部视觉细节已批准；
- 正式资产必须说明是原创重绘、重新建模，还是只提取了抽象视觉规律。

## 6. 本地二进制与 Git 边界

未明确允许公开再分发的图片可按项目规范存入：

```text
art/reference_library/
```

该目录用于本地分析并由 Git 忽略。以下内容不得因为“已经下载”而进入公开仓库或发布包：

- 原作立绘、皮肤、剧情 CG、UI 和游戏截图；
- 《群星》截图和原版资产；
- 网络建筑、舰船、材质、天文仪器和特效图；
- 用户提供但权利说明不完整的文件；
- `unknown`、`external_reference_only` 或只允许本地分析的素材。

仓库可以保存来源链接、事实性元数据、项目自行撰写的分析、Moodboard 结论和审核记录。任何例外都必须有可核验许可，并在资产登记表中落实。

## 7. 发生冲突时的优先级

1. 权利和许可限制优先于任何美术需求；
2. 已确认的原作角色识别事实优先于 AI 候选和项目自由发挥；
3. Art Bible 的公共规范优先于单张参考图的偶然风格；
4. 对应角色／舰船分册优先于通用模板；
5. 实际游戏可读性、性能和格式要求优先于只在大图成立的细节；
6. 尚未确认的决策保持待定，不用“看起来合理”强行补完。

## 8. 最小交接包

把任务交给新的画师、建模人员或 AI 工具时，至少提供：

- `ART_BIBLE.md`；
- `COLOR_SYSTEM.md`、`SHAPE_LANGUAGE.md`、`MATERIAL_GUIDE.md`；
- 对应角色或舰船分册；
- 本资产相关 Moodboard；
- 获准使用的 `reference_id` 列表及使用边界；
- `ART_STYLE_ANTI_PATTERNS.md` 中相关禁区；
- 最终游戏规格与 `ART_REVIEW_CHECKLIST.md` 当前阶段；
- 权利、AI 输入和正式资产登记要求。

只提供一张“喜欢的参考图”不构成有效美术委托。

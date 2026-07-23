# 现有视觉资源审计

> 审计日期：2026-07-22  
> 审计范围：`assets/`、`mod/gfx/`、`docs/art/reference_library/`，以及项目外目录 `C:/Users/Admin/Desktop/ppt/爱缪莎图册/`。  
> 本文只记录文件是否存在、可承担什么角色及仍需确认的事项，不对来源不明素材作授权判断。

## 1. 审计口径

本次审计把资源分为三层：

1. **参考来源**：原作画面、外部资料或经过筛选的视觉依据，用于分析，不等于可以随 Mod 分发。
2. **项目工作资源**：概念稿、预览渲染、Blender/OBJ 源文件、生成脚本和联系表，可用于继续制作与审核。
3. **正式游戏资产**：位于 `mod/gfx/`、已被游戏读取或准备被游戏读取的 PNG、DDS、Mesh、GFX 等文件。

必须特别强调：**正式游戏资产不自动等于参考来源，也不能反向证明其原始素材的来源或授权状态。** `mod/gfx/` 中的成品只能证明“项目已经做出了什么”，不能代替参考图库中的来源、权利状态和视觉分析记录。

状态含义：

- **已发现**：存在可识别文件，可进入后续登记或审核。
- **缺失**：在本次审计范围内没有找到对应材料。
- **待审核**：存在候选材料，但类别、来源、授权、可分发性或视觉用途尚未完整登记。

## 2. 总体结论

- `assets/official_reference/`、`assets/portrait/`、`assets/icon/` 目前只有 `.gitkeep`，尚未形成正式的原作参考库。
- `assets/ai_generated/destiny_lord/` 已形成较完整的舰船建模工作链；2026-07-22 起旧 Stage 9 退出“命运之主”身份，仅保留为技术工作资源并等待改作其他舰船。
- `assets/ai_generated/destiny_observatory/` 的旧建模方案与 Blockout 已正式废弃；文件只保留为历史记录，未来命运观测塔从零重设。
- `assets/ui/white_night_pavilion/` 有 UI 源图、地区联系表、派系图标与生成脚本；部分图片可能包含原作游戏画面或衍生整理，来源与可分发边界需单独复核。
- `mod/gfx/` 已有 228 个运行时/正式资源文件，其中大量为 PNG、DDS、Mesh 与图标。这些文件可以用于检查 Stellaris 技术规格和游戏内可读性，但不应被登记为原作或外部视觉来源。
- 项目外 `C:/Users/Admin/Desktop/ppt/爱缪莎图册/` 有 5 张爱缪莎 JPG，可作为本地候选参考；文件来源与再分发权未在仓库中登记，因此不得直接加入 Git。
- 七份专题 Moodboard 已存在，但大部分引用仍是“待登记参考 ID”，尚未与一份完成审核的 `REFERENCE_MANIFEST.csv` 建立闭环。
- 已建立项目自制中央庭公共材质校准板和黑门／异界第一版正式视觉对照组；它们是分析与校准文档，不是游戏正式资产。
- 没有发现独立的外部建筑、天文仪器、空间站资料集，也没有发现已登记的 Stellaris 官方技术参考截图集。

## 3. 分类审计总表

| 分类 | 状态 | 已发现证据 | 缺口与审核要求 |
|---|---|---|---|
| 原作角色基础立绘 | 待审核 | 项目外 `爱缪莎图册/` 有 5 张爱缪莎 JPG；`mod/gfx/models/portraits/` 有爱缪莎游戏用立绘 | 项目外图片均为哈希文件名，缺少原页面、标题、版本与权利说明；正式肖像不能代替原作来源登记 |
| 原作觉醒立绘 | 待审核 | 爱缪莎图册中有多张不同服装、姿态和特效的全身图候选 | 仅凭画面不能确认哪一张属于觉醒、突破或其他状态，需由熟悉原作的人员标注 |
| 原作皮肤 | 待审核 | 图册中可见蓝色礼服与竖琴、黑白礼服/舞台、休闲魔术师等不同造型候选 | 需补原作皮肤名、获得途径、是否限时及来源链接；不得凭视觉推断正式名称 |
| 原作剧情 CG | 待审核 | `7B05F4A725CC460B5EA0F9A0230F97C0.jpg` 为横向场景式图片候选；地区联系表含多张游戏场景画面 | 需确认是剧情 CG、皮肤插画还是宣传图；地区画面需登记截取来源与用途 |
| 原作神器与技能特效 | 待审核/缺失 | 爱缪莎候选图中有卡牌、星轨、月牙和玫红能量轨迹 | 尚无按技能、神器状态和时间点整理的截图组；单张立绘特效不足以支撑统一特效规范 |
| 原作环境与机构 | 待审核 | `assets/ui/white_night_pavilion/faction_icons/district_reference_contact_sheet.png` 含东方古街、中央城区、中央庭、旧城区、海上研究所、海湾侧城、高校学园等画面 | 联系表似由游戏画面拼合，但来源、截取方法、授权状态未登记；中央庭、研究所等需拆成可追溯条目 |
| 原作 UI、图标与字体氛围 | 待审核 | 地区联系表保留了原作界面布局；同目录有地区/派系图标工作文件 | 需要区分“原作截图”“项目重绘”“AI/脚本生成图”；字体和图标不得因已被裁切就默认可分发 |
| 黑门与异界表现 | 第一版基线已建立 | `docs/art/calibration/BLACK_GATE_OTHERWORLD_COMPARISON.md` 已按黑门、黑核、黑雾／环境、异界生态和工程响应分层，并登记原作文字证据入口 | 仍需按单张原作截图补来源、状态和校色，项目 SVG 不能替代原作图证 |
| Stellaris 舰船实现参考 | 待审核 | `mod/gfx/models/ships/destiny_lord/` 有 Mesh、贴图和预览；`assets/ai_generated/destiny_lord/` 有完整制作链 | 这些是本项目实现结果，不是 Stellaris 官方参考；仍缺普通舰、泰坦、主宰、巨像的可追溯技术参考组 |
| Stellaris 巨构实现参考 | 缺失/待审核 | `assets/ai_generated/destiny_observatory/DESTINY_OBSERVATORY_BLENDER_PLAN.md` 记录了低模、材质、动画、LOD 计划 | 只有项目方案，没有 Stellaris 巨构的尺度、构图和远景表现参考截图，也没有观测塔成品渲染 |
| Stellaris 星球、建筑、区划 | 待审核 | `mod/gfx/interface/icons/buildings/` 与 `districts/` 有大量正式图标 | 正式图标不是参考来源；缺少已登记的原版星球、区划、建筑图标构图与缩放对照 |
| Stellaris UI 与图标 | 待审核 | `mod/gfx/interface/icons/` 已覆盖科技、传统、飞升、法令、舰船部件等多类正式资产 | 可用于项目内部一致性检查，但缺少原版技术尺度、边框、安全区、缩放可读性的来源条目 |
| Stellaris 粒子与战斗特效 | 缺失 | 未发现独立整理的开火、命中、光束、弹体、引擎或光环参考 | 模型发光贴图只能说明静态材质，不能代替动态粒子参考 |
| Stellaris 考古与星界间隙 | 缺失 | 仅有分类说明文档 | 没有可追溯截图、场景帧或构图分析条目 |
| 现有 AI/生成式概念资源 | 已发现/待审核 | `assets/ai_generated/destiny_lord/` 有 4 张阶段预览；`assets/ui/white_night_pavilion/white_night_pavilion_generated_source.png` 为生成源图命名 | Stage 9 只保留为旧舰体技术演进证据，不再是命运之主视觉锚点；白夜馆源图的生成方式、模型、提示词与可分发边界未在同目录登记 |
| 舰船三视图或建模参考 | 已发现/待补 | 旧 Stage 9 有 `.blend`、`.obj`、`.mtl`、LOD0/1/2、分段船体和多阶段预览 | 可服务旧舰体改作其他舰种；未来命运之主必须另建正交图、比例尺、模块拆解与定位审核 |
| 配色板 | 第一版基线已建立 | `docs/art/calibration/CENTRAL_COURT_MATERIAL_CALIBRATION.md` 与 SVG 已记录公共颜色、材质职责和状态色 | 仍需代表性资产游戏内曝光校准；不得把项目校准板直接当正式贴图 |
| Moodboard | 已发现/待审核 | `docs/art/reference_library/moodboards/` 下已有 7 份专题文档 | 引用 ID 多为预留项；需在清单中绑定具体来源、权利状态与审核结论后才能升级为批准锚点 |
| 外部建筑参考 | 缺失 | 只有 `external/ARCHITECTURE.md` 分类说明 | 未发现已登记的照片、图纸或链接条目 |
| 外部材质参考 | 缺失 | 只有 `external/MATERIALS.md` 分类说明 | 未发现陶瓷装甲、玻璃、金属、半透明材料的具体条目 |
| 外部天文仪器参考 | 缺失 | 只有 `external/ASTRONOMY.md` 分类说明 | 未发现星盘、浑仪、轨道模型、观测设备的具体条目 |
| 外部空间站与工业设计参考 | 缺失 | 只有 `external/INDUSTRIAL_DESIGN.md` 分类说明 | 未发现空间站、灾害指挥中心、科研设施、博物馆陈列或工业产品条目 |

## 4. 已发现资源详表

### 4.1 项目外爱缪莎图册

本地目录：`C:/Users/Admin/Desktop/ppt/爱缪莎图册/`

| 文件 | 尺寸 | 画面层面可确认的内容 | 当前处理结论 |
|---|---:|---|---|
| `0E98F1698988D4D9F50F538510F78BE7.jpg` | 750×916 | 金色长发、黑/玫红/暗紫服饰、卡牌、星与月牙轨迹的全身图 | 可作为角色识别候选；具体原作状态、来源与权利待审核 |
| `721512BDB3BBA02A0396ACEAA6252895.jpg` | 750×916 | 黑红服装、卡牌与高饱和玫红能量轨迹的动态全身图 | 可作为技能特效与动态姿态候选；不可外推为全文明配色 |
| `7B05F4A725CC460B5EA0F9A0230F97C0.jpg` | 1334×750 | 室内舞台/会客空间、角色特殊服装的横向场景图 | CG、皮肤宣传图或其他类别待人工确认 |
| `C37365DF90F1C51CCFFC112C7146E882.jpg` | 750×914 | 蓝黑礼服、竖琴、花饰的全身图 | 特定服装参考候选；不得当作角色基础形态或文明公共风格 |
| `D94A3E2E48E3D627FA803F7D2ECEA95B.jpg` | 750×918 | 黑白服装、礼帽、卡牌与骰子的全身图 | 特定造型/皮肤候选；原名与来源待审核 |

这些文件位于 Git 仓库之外，且仓库内没有来源和授权记录。后续即使下载或复制到本地参考缓存，也只能放在被 `.gitignore` 排除的本地目录；在来源和再分发权明确前不得提交到公开 Git。

### 4.2 命运之主建模工作资源

主要目录：`assets/ai_generated/destiny_lord/`

已发现：

- 低模与精修源：`destiny_lord_blockout.blend`、`destiny_lord_stage2.blend`、`destiny_lord_stage3.blend`、`destiny_lord_stage4_lod.blend`、`destiny_lord_stage5_uv.blend`、`destiny_lord_stage6_materials.blend`、`destiny_lord_stage7_baked.blend`、`destiny_lord_stage8_pdx_ready.blend`、`destiny_lord_stage9_refined_A.blend`。
- 多级模型：`destiny_lord_lod0.obj`、`destiny_lord_lod1.obj`、`destiny_lord_lod2.obj`。
- 船体分段：Bow、Mid、Stern 的 OBJ/MTL 与 PDX 来源文件。
- 贴图：`textures/destiny_lord_basecolor.png`、`destiny_lord_emissive.png`、`destiny_lord_normal.png`。
- 阶段预览：Stage 2、Stage 3、Stage 6、Stage 9A，共 4 张 PNG。
- 制作脚本：Blockout、LOD、UV、材质、烘焙、PDX 准备、导出与校验脚本。

审计判断：这套文件已经足以作为**项目自身的技术参考和版本演进记录**，尤其适合验证网格、LOD 与导出流程；但它不是“原作参考”或“Stellaris 官方舰船参考”。2026-07-22 起 Stage 9 不再代表命运之主，其宽楔舰体、中央环、双侧环和旧材质不能进入新版命运之主规范。旧模型等待改作其他舰船，未来身份确定前仍缺对应正交图、比例尺、模块拆解、炮位定位和远景缩放对照。

### 4.3 命运观测塔

主要目录：`assets/ai_generated/destiny_observatory/`

已发现：

- `DESTINY_OBSERVATORY_BLENDER_PLAN.md`：低模、结构精修、材质、旋转动画、LOD、尺寸和交付计划。
- `blender_create_observatory_blockout.py`：Blockout 生成脚本。

审计判断：该方案已于 2026-07-22 废弃。上述文件只保留用于说明旧方案曾采用的结构拆分和技术流程，不得继续生成、精修或被引用为命运观测塔造型锚点。

未发现：

- 完整概念图或三视图。
- 可审核的 Blender 成品、OBJ、LOD 或渲染预览。
- 与 Stellaris 原版巨构尺度对照的参考条目。

### 4.4 白夜馆 UI 与地区画面

主要目录：`assets/ui/white_night_pavilion/`

已发现：

- `white_night_pavilion_generated_source.png`：1672×941 的生成源图。
- `create_white_night_ui.py`：事件背景、派系页面与图标组合脚本。
- `faction_icons/district_reference_contact_sheet.png`：960×1256 的地区画面联系表。
- `region_icon_sheet_source.png`、`white_night_faction_icon_sheet_source.png` 与多枚 256×256 图标。

风险与边界：

- 生成脚本和图标文件可以证明项目制作过程，但源图的生成工具、提示词、原始输入与权利状态仍需登记。
- 地区联系表视觉上包含游戏地区和 UI 画面，不能因为已经拼合或裁切就自动视为项目原创或可再分发素材。
- 若这些文件未来只作为参考，应迁移到本地不跟踪参考区；若继续作为正式资产，则必须进入正式资产登记并补齐来源审核。

### 4.5 `mod/gfx/` 正式资产

本次共发现 228 个文件，主要包括：

- 角色肖像与 Sprite 定义。
- 命运之主 Mesh、贴图和实体定义。
- 科技、传统、飞升、建筑、区划、法令、舰船部件等图标。
- 白夜馆事件背景。

它们的价值在于：

- 检查 DDS/PNG 配套、透明通道、路径、游戏内安全区和缩放可读性。
- 对照项目已实现的公共色彩、图标轮廓与发光强度。
- 检查源文件到游戏文件的导出关系。

它们不能承担：

- 原作角色或场景的来源证明。
- Stellaris 原版美术规范的来源证明。
- 外部参考图的授权证明。
- 参考图可以直接进入正式资产库的证明。

## 5. Moodboard 审计

已发现以下初始文档：

- `moodboards/CENTRAL_COURT.md`
- `moodboards/ARTIFACT_TECHNOLOGY.md`
- `moodboards/AEMUSA.md`
- `moodboards/ANTONIVA.md`
- `moodboards/DESTINY_SOVEREIGN.md`
- `moodboards/OLD_WORLD_ECHOES.md`
- `moodboards/OTHERWORLD_AND_ASTRAL_RIFTS.md`

这些文档已经提出关键词、色彩、形状、材质、光效、禁止项和适用范围，适合作为第一版决策框架。当前不足是：

1. 多数 `reference_id` 仍是预留主题，不代表已有真实文件。
2. 没有一份完成审核的清单证明每个 ID 的来源、权利与允许用途。
3. 部分结论来自现有设计讨论，应明确区分“项目决策”与“原作事实”。
4. Moodboard 只能在引用条目完成审核后升级为稳定视觉锚点。

## 6. 当前缺失清单

优先缺失：

1. 安托涅瓦及其他核心角色的可追溯基础/觉醒/皮肤参考。
2. 神器本体、技能阶段、命中特效和黑门动态表现的分组截图。
3. 交界都市环境、机构室内外、生活性设施的来源化环境参考。
4. Stellaris 普通舰、泰坦、主宰、巨像的远景剪影与技术尺度对照。
5. Stellaris 巨构、考古、星界间隙、建筑/区划、粒子特效的实现参考。
6. 从零重设后的命运之主正交三视图、尺寸基准、模块拆解和武器定位图；旧 Stage 9 不计入完成度。
7. 从零重设后的命运观测塔概念图、三视图、Blockout 渲染和尺度对照；旧案不计入完成度。
8. 中央庭公共校准板已经建立初版，仍缺角色个人配色与公共配色的完整边界表及游戏内校色结果。
9. 天文仪器、灾害指挥中心、空间站、科研设施、博物馆、材料与工业设计的外部参考。

## 7. Git 与权利边界

1. `C:/Users/Admin/Desktop/ppt/爱缪莎图册/` 当前不在仓库内，应继续保持本地状态，直至来源和再分发权完成审核。
2. 后续允许联网下载的来源不明、仅供分析或禁止再分发图片，应保存到项目约定的本地不跟踪目录，例如 `art/reference_library/`，并由 `.gitignore` 排除。
3. `copyright_or_license_status = unknown` 不得被自动改写为 `licensed`、`user_owned` 或“可随 Mod 分发”。
4. 原作截图可登记为视觉参考，但不能因其属于官方游戏就自动复制到正式资产目录。
5. 参考图只有在重新绘制、重新建模、权利审核和游戏规格审核完成后，才可另行登记为正式资产；不能直接从参考目录复制到 `mod/gfx/`。
6. 已经位于 `mod/gfx/` 的正式文件仍需追溯其制作来源；“已经在游戏中运行”与“具有公开分发权”是两个不同判断。

## 8. 后续审核优先级

### P0：建立可追溯边界

- 为现有 5 张爱缪莎候选图补来源、原作状态、用途与权利状态，但不把原图加入 Git。
- 核查白夜馆生成源图与地区联系表的来源；决定其属于本地参考还是正式资产。
- 将 `mod/gfx/` 中正式资产与参考清单彻底分开。

### P1：补技术参考

- 建立 Stellaris 舰船、巨构、UI、粒子和远景缩放参考组。
- 待新版概念批准后，为从零重设的命运之主建立三视图、模块拆解、炮位和 LOD 对照。
- 待新版概念批准后，为从零重设的命运观测塔建立概念图、Blockout 预览与巨构尺度对照。

### P2：补公共视觉语言

- 以现有中央庭公共材质校准板为初版基线，补游戏内校色和正式资产审核；神器技术配色仍需独立完善。
- 补建筑、材料、天文仪器、科研空间和博物馆陈列参考。
- 将所有 Moodboard 的预留 ID 替换为已经登记和审核的真实条目。

完成上述审核前，现有文件可以支持继续开发，但不能被视为一套来源完整、权利边界清晰的参考图库。

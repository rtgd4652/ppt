# 《神器使》Stellaris Mod 知识库总索引

本目录保存项目可审查的知识成果，包括来源清洗、人工校订、原作事实、项目正史、角色档案与系统转译。

知识库的目标不是把所有材料混成一份“唯一设定”，而是让每条结论都能回答：

1. 它来自哪里？
2. 它是否经过人工审核？
3. 它属于原作事实、项目解释还是 Mod 设计决定？
4. 它是否仍有未解决的冲突或谜团？
5. 它如何被后续角色、剧情、美术和游戏系统使用？

## 1. 核心原则

### 1.1 可审查文件是知识依据

知识依据由仓库中的来源记录、结构化 JSON、clean Markdown、人工校订文档和项目正史圣经共同组成。

本地 SQLite 数据库只负责：

- 建立结构化索引。
- 支持检索、关系查询与完整性检查。
- 帮助工具定位来源、术语和审核状态。

**数据库不是知识真源。**

数据库二进制文件不提交到 Git，并且应当能够由已提交的 Markdown、JSON、来源索引和工具脚本重新生成。数据库记录与可审查文件冲突时，应回到来源及清单修正，不得直接把数据库中的结果视为更高层事实。

### 1.2 三类知识必须分开

| 层级 | 含义 | 主要位置 |
| --- | --- | --- |
| 原作事实 | 由 Wiki 文本、人工确认视频片段或其他登记来源直接支持的内容 | `raw/`、`indexes/`、`story/pages/`、`curated/` |
| 项目解释与项目正史 | 项目对原作信息的结构化整理，以及为星际时代延伸所确认的正史 | `world/`、`timeline/`、`organizations/`、`story/*_bible*` |
| 系统与设计转译 | 将知识转化为角色定位、白夜馆入口、Stellaris 内容或美术设计的工作层 | `mod_ready/`、`systems/`、标准角色档案及仓库 `docs/` |

设计转译不能反向改写原作事实；项目正史不能伪装成原作原文；尚未解决的谜团不能仅因实现需要被自动定论。

## 2. 推荐阅读顺序

新加入项目的编剧、策划、开发者、画师或代理，应按以下顺序阅读。

### 第一步：来源与清洗证据

先确认材料本身和采集边界：

1. [`../raw/huiji/`](../raw/huiji/)

   灰机 Wiki 原始采集层，用于回溯页面内容；不直接作为最终摘要。
2. [`../indexes/story_pages/`](../indexes/story_pages/) 与 [`../indexes/images/`](../indexes/images/)

   页面来源和图片信息索引，保存来源定位；图片索引不代表素材拥有公开再分发授权。
3. [`story/pages/`](story/pages/)

   Wiki 剧情页面的 clean 正文层。
4. [`characters/`](characters/) 中的中文角色资料

   角色页面清洗结果，与 `raw/huiji/characters/` 和图片索引共同构成角色采集三件套。
5. [`curated/sources/`](curated/sources/)

   来源身份、适用范围和局限说明。

这一层回答“页面或材料写了什么”，不负责决定 Mod 正史。

### 第二步：原作事实与人工审核层

再阅读人工审核规则、术语和剧情校订：

1. [知识库治理规范](curated/governance/knowledge_governance_v0.1.md)

   了解来源优先级、事实卡、审核状态与正式设定重建规则。
2. [核心术语库](curated/glossary/core_terms_v0.1.md)

   了解原作事实、项目解释、设计决定的术语分层及歧义边界。
3. [核心术语审核队列](curated/glossary/core_terms_review_queue_v0.1.md)

   查看仍待直接来源或跨资料核验的术语。
4. [`story/curated/days/`](story/curated/days/)

   按单日整理的人工校订剧情。
5. [`story/curated/finales/`](story/curated/finales/)

   最终日、结局和特殊灭世整理。
6. [`story/curated/structure/`](story/curated/structure/)

   路线分支、选择树与七日结构说明。
7. [项目编辑决定](curated/decisions/project_editorial_decisions_v0.1.md)

   记录项目采用、排除或暂缓的编辑范围；这些决定不是原作事实。

随后阅读本轮建立的第一份总控文档：

- [原作事实／项目正史／开放谜团矩阵 v0.1](world/fact_canon_mystery_matrix_v0.1.md)

该矩阵用于判断一个概念当前属于：

- 已有直接依据的原作事实。
- 已确认的项目正史。
- 仍需保持开放的谜团。

如需写新设定，应先在矩阵中确认其层级和状态。

### 第三步：项目正史圣经

按以下顺序理解本项目从原作历史延伸至 Stellaris 开局的正史。

#### A. 基础世界观

1. [世界观圣经 v0.1](world/lore_bible_v0.1.md)
2. [神器体系设定圣经 v0.1](artifacts/artifact_bible_v0.1.md)
3. [剧情与历史整合圣经 v0.1](story/story_bible_v0.1.md)
4. [组织体系设定圣经 v0.1](organizations/organization_bible_v0.1.md)
5. [历史时间线圣经 v0.1](timeline/timeline_bible_v0.1.md)

这些文档提供已有基础定义；遇到与更细化文档不同的表述时，应先检查事实层级与更新时间，不应直接覆盖。

#### B. 本轮四份基础文档

1. [原作事实／项目正史／开放谜团矩阵 v0.1](world/fact_canon_mystery_matrix_v0.1.md)

   先确定哪些内容可确认、哪些属于项目延伸、哪些必须保持未知。
2. [灾后至星际时代详细时间线 v0.1](timeline/post_disaster_to_interstellar_timeline_v0.1.md)

   理解轮回终止、灾后稳定、重建、制度化、全球整合、太阳系探索与 Stellaris 开局之间的阶段关系。
3. [中央庭国家与制度设定圣经 v0.1](organizations/central_court_state_bible_v0.1.md)

   理解中央庭从危机组织发展为统一人类星际国家治理核心的制度边界。
4. [宇宙论圣经 v0.1](world/cosmology_bible_v0.1.md)

   理解黑门、异界、箱庭、世界之主、世界重构、世界线与命运规则之间当前能够确认的最小关系。

推荐顺序是“矩阵 → 时间线 → 国家制度 → 宇宙论”。

宇宙论中的开放谜团不得反向填入时间线或国家制度，除非先完成来源核验和正史审核。

### 第四步：角色、系统与设计转译

在掌握事实层和项目正史后，再进入实现导向资料。

#### 角色标准资料

- [角色设计统一模板](characters/character_design_template_v0.1.md)
- [角色名单](characters/character_roster_v0.1.md)
- [核心人物关系圣经](characters/character_relationship_bible_v0.1.md)
- [爱缪莎标准角色档案](characters/aemusa_character_v0.1.md)
- [安托涅瓦标准角色档案](characters/antoniva_character_v0.1.md)
- [晏华标准角色档案](characters/yanhua_character_v0.1.md)

标准角色档案用于描述角色在项目正史中的历史与叙事位置，不等同于技能、数值或事件实现。

#### Mod Ready 摘要

- [`mod_ready/characters/`](mod_ready/characters/)

该目录保存将 clean 角色资料整理为 Stellaris 可用方向的摘要。它属于设计候选层，不是原作事实，也不能覆盖标准角色档案和项目正史圣经。

#### 功能系统

- [白夜馆系统说明](systems/white_night_hall.md)

白夜馆仅是神器使招募、联络、档案展示与管理的功能入口，不属于中央庭或任何世界观组织。

#### 仓库设计文档

具体游戏设计、美术规范、路线图和版本计划位于仓库 [`../docs/`](../docs/)。进入代码或资产制作前，应同时核对相应设计文档与本知识库中的事实边界。

### 第五步：数据库与工具索引

最后阅读数据库和同步工具说明：

1. [本地 SQLite 数据库说明](database/README.md)
2. [知识库工具说明](../tools/knowledge/README.md)
3. [`../tools/knowledge/data/`](../tools/knowledge/data/) 中的结构化清单和种子
4. [`../tools/knowledge/scripts/`](../tools/knowledge/scripts/) 中的同步、初始化与检查工具

数据库适合：

- 快速检索术语、来源、剧情页和关系。
- 检查引用是否可解析。
- 验证清单归属、外键与重复项。
- 为后续工具提供结构化入口。

数据库不适合：

- 替代原始来源。
- 自动决定原作事实。
- 自动提升人工审核状态。
- 绕过 Markdown 和 JSON 的代码审查。
- 直接生成未经人工确认的项目正史。

## 3. 目录职责速查

| 路径 | 职责 | 是否可直接作为项目正史 |
| --- | --- | --- |
| `../raw/` | 原始采集与回溯 | 否 |
| `../indexes/` | 来源、页面和图片定位索引 | 否 |
| `characters/*.md` 中文 clean 文件 | 角色清洗资料 | 否，需审核与转译 |
| `story/pages/` | 剧情 clean 正文 | 否，需人工校订 |
| `story/curated/` | 人工整理的剧情、结局和结构 | 可作为事实审核依据，需保留路线范围 |
| `curated/sources/` | 来源身份与适用边界 | 否，用于证据治理 |
| `curated/glossary/` | 规范术语、边界与审核状态 | 按每条术语的知识层级使用 |
| `curated/decisions/` | 项目编辑选择 | 仅约束项目范围，不是原作事实 |
| `world/` | 世界观矩阵、世界观圣经与宇宙论 | 其中明确标注的项目正史可用 |
| `timeline/` | 历史阶段与详细时间线 | 其中明确标注的项目正史可用 |
| `organizations/` | 组织和国家制度圣经 | 其中明确标注的项目正史可用 |
| `artifacts/` | 神器体系圣经 | 其中明确标注的项目正史可用 |
| `mod_ready/` | 游戏转化候选 | 否 |
| `systems/` | 功能系统边界 | 仅约束对应系统 |
| `database/` | 本地数据库说明与不提交的派生索引 | 否 |

## 4. 冲突处理顺序

发现资料冲突时，不要直接选择“更新”或“更完整”的一句覆盖另一句。应按以下顺序处理：

1. 回到 `raw/`、来源索引和 clean 页面确认采集是否正确。
2. 检查剧情路线、日期、选择分支、说话者和结局范围。
3. 查看 `curated/` 中是否已有人工作出的确认、排除或特殊补充。
4. 查看核心术语及其审核状态。
5. 在事实／正史／谜团矩阵中确认该问题属于哪一层。
6. 若仍无法解决，保留为开放谜团或审核事项，不擅自定论。
7. 只有在来源与层级明确后，才更新项目正史或设计转译。

## 5. 新文档接入要求

新增知识文档时，应至少说明：

- 文档用途。
- 知识层级。
- 参考来源或上游文档。
- 已确认结论。
- 仍未确定的问题。
- 与现有文档发生冲突时的处理方式。

新增项目正史前，应先检查：

- [事实／正史／谜团矩阵](world/fact_canon_mystery_matrix_v0.1.md)
- [核心术语库](curated/glossary/core_terms_v0.1.md)
- 相应来源和人工校订资料

新增系统或游戏内容前，应再检查：

- 对应角色或世界观圣经。
- `mod_ready/` 中的转译摘要。
- 仓库 `docs/` 中的当前版本设计和实现边界。

## 6. 当前基础阅读链

```text
原始采集与来源索引
        ↓
Clean 正文与角色资料
        ↓
人工校订、术语与审核状态
        ↓
原作事实／项目正史／开放谜团矩阵
        ↓
灾后至星际时代详细时间线
        ↓
中央庭国家与制度设定
        ↓
黑门、箱庭、世界之主与命运规则宇宙论
        ↓
角色档案、系统说明与 Mod Ready 转译
        ↓
Stellaris 脚本、美术与游戏资产
```

SQLite 数据库在这一阅读链旁提供检索与验证支持，不位于知识权威链的顶端。

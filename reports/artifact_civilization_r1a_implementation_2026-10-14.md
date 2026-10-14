# R1a前期公共基础源码接入

2026-10-14。接续用户“继续”，按已保存规格接入基准观测、标准件与公共服务。当前为源码接入、静态核账通过，`runtime_status = pending`，尚无新游戏或存档证据。

## 新增内容

| 内容 | 已接入源码 |
| --- | --- |
| 研究3项 | 基准观测与仪器标定、前线维修与标准件、殖民地公共服务 |
| 建筑4座 | 基准观测站、标准件工坊、社区公共服务中心、基础民生工场 |
| 岗位4类 | 初级观测员、标准件技工、社区协调员、民生技工 |
| 界面引用 | 30个中文键、11个独立GFX别名，全部指向已存在纹理；未生成或替换图像 |

当前公共科技总数22项，行星建筑定义19个；2项遗留科技仍单列，个人研究未实现。完整路线目标仍为72项公共科技、27类46阶段建筑，未把源码接入视为运行或平衡验收。

## 行为与兼容

三项新研究只读取文明身份、原生科研层级及明确科技前置。建筑用原生`prerequisites`显示研究解锁，提供有限低级岗位；不读取角色等级、组合或个人授权。

基准观测站→原黑门观测站，标准件工坊→原神器工坊，基础民生工场→原民生工坊。三个旧高级建筑新增显式`can_build = yes`，保留原直接建造资格；原费用、建时、科研检查、岗位及其余字段未变。下级检查高级存在与高级施工队列，并连接原生升级链；同族上限及高级直建、升级交互仍需在游戏中确认。

社区协调员舒适度通过岗位`triggered_planet_modifier`提供，未加到建筑常驻修正；实际就业与产出尚未验证。岗位数与资源按设计的脚本基准实现，不推定为4.5界面显示的人口数量。

R1b的样本库、档案室、四项研究与主动项目均未实现。无新事件、月度回调、免费研究发放或存档迁移；C2、既有角色工坊、主线及连续巨构未修改或重测。

## 文件与验证

- [科技](../mod/common/technology/artifact_public_foundation_technology.txt)、[建筑](../mod/common/buildings/artifact_public_foundation_buildings.txt)、[岗位](../mod/common/pop_jobs/artifact_public_foundation_jobs.txt)。
- [中文](../mod/localisation/simp_chinese/artifact_public_foundation_l_simp_chinese.yml)、[图标别名](../mod/interface/artifact_public_foundation_icons.gfx)。
- `python -B tools/validation/check_mod.py --game-dir F:/steam/steamapps/common/Stellaris`：通过；121脚本、243事件、1468中文键，显式图像目标存在。非本地化TXT／GFX为UTF-8无BOM，中文YML有BOM。
- 定向按解析结构核对：新研究成本、层级、前置；建筑造价、维护、岗位；岗位资源和升级目标均与[规格](../docs/design/artifact_civilization_r1_implementation_spec_v0.1.md)一致。旧15个建筑仅三个对象多了`can_build=yes`；旧科技与旧岗位结构保持。结果见[静态核账](artifact_civilization_r1a_static_2026-10-14.json)。
- 使用`stellaris-script`技能，并对照本机4.5.2的`common/buildings/00_example.txt`、`05_research_buildings.txt`、`common/pop_jobs/02_specialist_jobs.txt`及科技类别定义。原版示例与静态通过不能证明本包引擎行为已通过。

本批之前的基准提交为`056801e`；本批源码由包含本报告的中文提交定位。另一工作线的未跟踪连续巨构目录保持原状。

## 下一步

接R1b的其余四项研究、两座低级建筑、初级档案员及本地项目。项目实现后合并安排一次新增正常路径和有保存意义的关键读档，避免每座楼各跑一轮历史验收；优先核对同族上限、原高级直建与一次代表升级，发现实际失败再定向修复。图标批量仍暂停。

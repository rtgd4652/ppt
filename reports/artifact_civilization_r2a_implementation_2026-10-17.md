# R2a矿脉开发与循环回收源码交付

2026-10-17，接续R1代表流程保存点dacd239。已完成R2首个小包规格与源码，source_status为implemented_static_checked，runtime_status和balance_status均pending。本批没有操作游戏、载档或生成图片；不把R1存档及读档证据当作R2a运行证明。

本包新增2项公共科技、2座设施、2类专家岗位和16个中文键。公共当前28项科技、23个建筑定义，另2项遗留科技不计入公共树；完整72项科技／27类46阶段建筑目标不变。人物组合、连续巨构、批量图标继续暂停，个人路线仍独立。

B10精准矿脉测绘接B07，工程T2、1200科研、110权重；解锁矿脉测绘站，建设费600矿物／100能源、300日、3能源维护，提供200劳动力单位测绘员。每100单位产出6矿物／1工程，维护1能源／0.5消费品。当地已建普通district_mining才能新建，复用城市槽resource集合；不新增区划，也不把在建升级条件放进potential。取得原B04科技后可升级旧相位矿站。

B12副产物闭环利用接B10＋C07，工程T3、3000科研、95权重；解锁循环回收处理厂，800矿物／100合金、360日、4能源维护。有普通采矿区或有效矿脉／基础工业设施时提供200回收技师容量；每100单位消耗2能源／1消费品，产出4矿物／0.5合金。has_active_building排除停用或损坏建筑；没有合格来源时停岗，但建筑与4能源维护保留。回收厂不能自作来源，不增加垃圾货币、一次性资源、退款、工程结算或月度事件。

原相位矿站仅两项变更：增加can_build=yes保留原科技直接建造；job_artifact_phase_miner_add从8改为800。原字段8是4.5实际劳动力容量，新低级楼200单位若直接衔接会倒挂；本机原版b1_jobs为200，故在这一条升级链落实单位衔接。**当前4.5高级站容量实际扩大100倍，可能吸收更多人口并显著改变产出与维护，不是无影响显示修正。** 原600日、2400矿物／500合金、20能源维护、旧B04科技与每100单位矿工资源全部保持，旧矿站无需补研或重建。其他建筑族的旧容量未调整，另列迁移核对；本包未做自然经济平衡验收。

R2全部13节点已按依赖拆为R2a（B10／B12）、R2b（A05／B09）、R2c（A06／A07／E06）、R2d（B11／C09／C10／E04／E05／E07）。仅R2a实现；后续多源比对、预警风险、物资预留和城市方案需先明确具体能力，不把路线描述直接当作现成机制。

新增源码：

- mod/common/technology/artifact_midgame_resource_technology.txt
- mod/common/buildings/artifact_midgame_resource_buildings.txt
- mod/common/pop_jobs/artifact_midgame_resource_jobs.txt
- mod/localisation/simp_chinese/artifact_midgame_resource_l_simp_chinese.yml

修改旧矿站位于mod/common/buildings/aemusa_buildings.txt。直接引用现有2科技／2建筑DDS名称，岗位借用原版miner／artisan图标，无新增GFX别名、纹理或候选安装。资产清单只更新当前数量。

结构核账通过：131脚本、249事件、1544本地化键、791登记／734引用状态。3项R2a实际条件夹具通过；AST逐项对照规格、前置、费用、产出和维护，13节点拆包前置顺序无遗漏或重复。其余14座旧建筑AST相同；原科技文件、旧岗位文件、R1建筑文件逐字节不变；旧矿站除上述两项外全部字段相同。新引用DDS文件存在。证据见[静态核账](artifact_civilization_r2a_static_2026-10-17.json)。未重跑R1／C2／人物历史测试。

已核对本机4.5.2生成的triggers.log中has_district、has_active_building支持planet／ship／colony；原版00_scripted_variables的b1_jobs=200；zone_urban使用排除列表且未排除resource，保持旧矿站集合；原版资源建筑存在triggered_planet_modifier条件修正。技能参考为本地stellaris-script的科技／建筑／岗位示例及依赖表。以上只支持源码选型，不证明原生动态更新、建筑列表、就业或存档恢复已通过。

下一次先正常冷启动加载新源，再做一条新增正常研究—建造路径、一次矿站正常升级，唯一关键读档选在升级已有进度时；核对实际就业与容量替换、回收来源资格及严重失败点。资源不足按用户授权直接rr并记录，不再反复操作市场。其他特殊世界、倍率、历史项目不扩测。当前R1结果2259.07.28仍为保留的暂停点，不需要重做R1。

完整字段、实际容量迁移和边界见[R2a规格](../docs/design/artifact_civilization_r2a_implementation_spec_v0.1.md)与[结构化规格](../docs/design/artifact_civilization_r2a_implementation_spec_v0.1.json)。

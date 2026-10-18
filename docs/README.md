# 项目文档索引

更新：2026-10-10。本文只负责导航，当前状态统一维护在 [PROJECT_STATUS](PROJECT_STATUS.md)。

## 进入项目

- [架构与模块边界](ARCHITECTURE.md)
- [当前进度](PROJECT_STATUS.md)
- [智能体可用操作与接手说明](AGENT_OPERATIONS.md)：已验证能力、脚本入口、当前会话差异及失败处理；历史操作不自动重放。
- [内部里程碑与发布计划](ROADMAP.md)
- [当前执行清单](TODO.md)
- [只读检查与本地快照](../tools/validation/README.md)

## 设计与实施

- [R2e公共成果归档与研究园区规格](design/artifact_civilization_r2e_implementation_spec_v0.1.md)：真实成果、跨殖民地复现与本族升级；[源码保存](../reports/artifact_civilization_r2e_implementation_2026-10-18.md)、[代表运行](../reports/artifact_civilization_r2e_runtime_2026-10-18.md)及[检查点](../reports/artifact_civilization_r2e_checkpoint_2026-10-18.json)区分受控研究、样本正常流程和未扩测的材料分支。

- [1.0 叙事约束](design/v1.0_narrative_constraints.md)
- [主线工作包及授权记录](design/aemusa_main_story_implementation_work_packages_v1.0.md)
- [AWP-06 专属危机机制提案](design/aemusa_main_story_awp_06_mechanism_proposal.md)
- [主线接口契约](design/aemusa_main_story_implementation_interface_v1.0.md)
- [机器可读状态登记](design/aemusa_main_story_state_registry_expanded_v1.0.csv)
- [十名角色完成矩阵](../knowledge/characters/v1.0_character_completion_matrix.md)
- [十名神器使首版玩法](mechanics/artifact_users_play_guide_v1.0.md)
- [领袖成长与职责说明](mechanics/leader_growth_and_duty_v1.0.md)
- [成长与自由组合提案](design/artifact_civilization_growth_and_combinations_v0.1.md)
- [文明研究、传统与飞升实际路线](mechanics/artifact_civilization_route_v0.1.md)：19项文明科技、公共飞升、个人转变专属研究及2项遗留科技的边界；[C1记录](../reports/artifact_civilization_route_c1_2026-10-10.md)保存说明修正，[科技分离记录](../reports/artifact_technology_separation_2026-10-10.md)保存本次用户决定与文件拆分。
- [C2殖民地应急预案](../reports/artifact_civilization_emergency_c2_2026-10-10.md)：当地中枢的付费准备、限时保护与重新整备；源码及定向检查已通过，游戏流程和真实读档待验。
- [十人成长基准B1记录](../reports/artifact_growth_batch_b1_2026-10-09.md)：名册和公共计算已接入；各人的分级核心效果从B2继续，正式固定搭档按原著决定。
- [成长核心B2首批记录](../reports/artifact_growth_batch_b2a_2026-10-09.md)：安的时序记录按取得时档位提供有限用途，丽按实际成长推进付费施工；加载和页面检查与完整运行边界见报告。
- [B2首批10月10日运行与续接](../reports/artifact_growth_batch_b2a_runtime_2026-10-10.md)：安／丽档1正常流程、一次进行态读档和有限效果已通过，后续第二批复用；Computer Use与键盘限制已同步。
- [B2第二批实现与续接](../reports/artifact_growth_batch_b2b_2026-10-10.md)：其余八人的分级核心、启动深度修复、名册及赛斯代表流程／完成档载回通过；人物组合按用户要求暂缓。
- [10月9日收工与续接](../reports/development_closeout_2026-10-09.md)：A批、B1、B2源码检查点与当晚用户决定的历史记录；其中待补游戏检查已由10月10日记录接续。
- [首都工坊试验玩法](mechanics/artifact_engineering_play_guide_v0.1.md)：A批丽／安单人或自由协作；[运行记录](../reports/artifact_engineering_batch_a_2026-10-09.md)区分受控研究前置与正常月度工作。
- [知识库与正史入口](../knowledge/README.md)

## 美术与验收

- [Art Bible](art/ART_BIBLE.md)
- [资产生产需求](art/ASSET_PRODUCTION_PLAN.md)
- [里程碑4首批外观方案](art/MILESTONE4_VISUAL_PROPOSAL.md)：新旗舰、两阶段枢纽与代表肖像的制作接口及概念草案。
- [里程碑4首批制作与运行记录](../reports/milestone4_portraits_and_graybox_2026-10-08.md)：三套透明肖像、新档读回、独立Blender灰模与PDX导出；正式模型未接入游戏。
- [里程碑4六人肖像补齐](../reports/milestone4_remaining_portraits_2026-10-08.md)：安、赛斯、幽桐、格蕾莎、雯梓、丽正常通讯与统一新档读回；十人透明肖像现已接通，下一批进入正式模型。
- [新舰与枢纽材质样品续接](../reports/milestone4_surface_assets_2026-10-08.md)：五网格／三张DDS与独立实体样品，Blender离线预览；运行接入和游戏显示待做。
- [既有资产登记](art/ASSET_REGISTRY.csv)
- [参考图库](art/reference_library/README.md)
- [AWP-02 运行验收报告](../reports/aemusa_main_story_awp_02_validation_report.md)
- [十人首版统一收口](../reports/milestone3_ten_character_closeout_2026-10-07.md)
- [全线测试模板](../reports/aemusa_main_story_test_report_template_v1.0.md)
- [战争与天灾适配专项测试计划](../reports/aemusa_main_story_adapter_test_plan_v1.0.md)
- [本次整理与验证记录](../reports/project_architecture_review_2026-09-26.md)

## 历史资料

`project/history/` 保存本次整理前的 README、进度、路线图与 TODO。`DESIGN.md`、`project/project_status_v0.1.md`、`project/development_roadmap.md` 和旧封版文档保留历史语境，不决定当前任务顺序，也不授权恢复旧舰船、旧巨构或发布标签。

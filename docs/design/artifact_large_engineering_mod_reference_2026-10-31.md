# 大型工程的Mod实现参考

2026-10-31。用户要求：参考其他大型Mod的实际写法，避免把开发耗在繁琐测试上。本轮只读本机安装副本，对照E09与后续空间工程；代码基线为`1a90c09`，没有修改运行脚本、操作游戏或重测旧包。

## 已读来源

| Mod | 本机描述文件 | 本次查看的内容 |
| --- | --- | --- |
| Gigastructural Engineering & More | Workshop `1121692237`；版本`3.40.4`，声明`v4.5.*` | 超结构装配场的原生阶段链、阶段费用与完成回调；巨构飞升的建造上限；额外施工资源系统 |
| Ancient Cache of Technologies（ACOT） | Workshop `1419304439`；版本`4.*`，声明`v4.4.*` | Amerigo设施的分级研究、升级来源、费用、工期、收益和完成通知 |

以上是本机副本，不代表线上最新版。ACOT用于参考结构，不能据其版本声明认定4.5兼容。Workshop源码未复制进项目，也未改动这些Mod。

## 实际写法与借鉴

1. **把普通分段施工交给原生升级链。** Gigas的`hyperstructural_ass_0`至`_4`通过`upgrade_from`串联，各段定义`build_time`和`resources`，同时对应各自模型。见[装配场定义](/F:/steam/steamapps/workshop/content/281990/1121692237/common/megastructures/zz_i_hyperstructural_assembly.txt:199)。这支持我们用原生阶段承接空间工程的施工进度和升级入口，额外状态只记录工程特有的结果。

2. **特殊预算和特殊效果仍保留脚本。** 同一Gigas实例在`possible`检查额外材料，在`on_build_start`处理专用材料，在`on_build_complete`执行现场变化及通知。它不是纯原生、零脚本方案。我们的B14真实备料可作为特殊投入接入，但普通合金／工期尽量交给原生字段，避免同一费用重复扣除。

3. **完成名额与具体工程能力分开。** Gigas的`ap_gigastructural_constructs`直接提供`country_megastructure_build_cap_add = 1`，见[飞升定义](/F:/steam/steamapps/workshop/content/281990/1121692237/common/ascension_perks/giga_ascension_perks.txt:17)。这再次确认E09采用的字段确有使用先例；不能据此把本项目建筑供源、实际队列或与其他Mod兼容标为运行通过。

4. **升级本身可以承担清晰的技术阶段。** ACOT的`acot_amerigo_ae`由`acot_amerigo`升级，要求对应研究，直接定义1800日工期与资源费用，完工发送通知；后续`_se`继续同一链。见[Amerigo升级定义](/F:/steam/steamapps/workshop/content/281990/1419304439/common/megastructures/acot_megastructures.txt:2388)。借鉴研究—阶段—能力的结构，数值、资源和设定仍按本Mod设计。

5. **复杂替代系统只在确有玩法价值时采用。** Gigas另外有一套按国家条件启用的施工资源与进度重算逻辑，读取建造上限并统计在建巨构、分配进度。见[额外施工系统](/F:/steam/steamapps/workshop/content/281990/1121692237/common/scripted_effects/giga_alternate_mega_build_effects.txt:188)。这种体系服务于它自身规模；当前无需为单人Mod复制全局资源模型与扫描。

## 对本项目的决定

- **E09首版保持为营建基础。** 当前是行星营建项目，最终提供额外巨构并行容量；已有源码和检查结果保留。停止为这项容量继续增加付款确认、管理分支或专门回归，不把营建场计为正式神器奇观完成。
- **真正的空间巨构优先采用原生`upgrade_from`、费用、工期和完成回调。** 项目现有现实基线枢纽已经使用这种结构，见[枢纽运行态](/C:/Users/Admin/Desktop/ppt/simple_leader_edict/mod/common/megastructures/aemusa_reality_baseline.txt:126)。后续从自身已有结构和上述实例出发，避免重新维护一套通用施工计时器。
- **每个阶段应有用途。** 让阶段体现可见结构、可用功能或明确的资源选择；仅为了延长等待而重复点击的步骤不再扩展。神器巨构仍遵守“完成后获得此前没有的能力”，不只堆产出或容量。
- **公共与个人路线保持分离。** 下一项仍是D13公共舰体承载；正式巨构按各自能力设计接入。用户独立的连续巨构原型继续暂停。

## 最小验证与后续复用

这次为只读参考和文档调整，只检查新增引用与差异；不新增测试、不开游戏、不重复运行E09已有检查。

后续改动先做必要的语法／引用／编码检查。只有实际新增扣费、奖励或持久状态风险才补定向检查。原生升级、支付和进度不另写一套模拟器；在约20分钟阶段试玩中取一条正常建造／升级到核心能力生效的路径。有新增保存语义时做一次关键读档；崩溃、卡死、重复奖励或存档损坏定向处理，其余未验如实保留。

当前读取结果可直接复用，换AI不重新扫描整个Workshop，不按每种资源、每个阶段和每个窗口分别存档或穷举。后续只在具体缺口处补读相关源码。开发规则见[工作流](../DEVELOPMENT_WORKFLOW.md)，E09参数与证据边界见[规格](artifact_civilization_r4c_implementation_spec_v0.1.md)。

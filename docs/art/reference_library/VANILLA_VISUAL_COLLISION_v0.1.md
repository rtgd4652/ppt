# 原版视觉撞车库 v0.1

2026-10-31。[结构化入口](VANILLA_VISUAL_COLLISION_v0.1.json)。目前完成六组本机原生定义定位，网格/截图的目视对照仍待进行；没有把“源码里找到entity”当作辨识度通过。

| 编号 | 本机原生定义 | 后续对照问题 |
| --- | --- | --- |
| VV-01 | `common/megastructures/00_ring_world.txt` | 圆形空间结构的用途与主轮廓 |
| VV-02 | `common/megastructures/03_think_tank.txt` | 核心/支臂/科研平台的主次关系 |
| VV-03 | `common/megastructures/02_spy_orb.txt` | 观测系统的悬浮层级与中心识别 |
| VV-04 | `common/megastructures/07_strategic_coordination_center.txt` | 军事指挥设施的工程框架 |
| VV-05 | `common/megastructures/habitats.txt` | 居住设施、对接与维护空间 |
| VV-06 | `common/megastructures/16_cosmogenesis_world.txt` | 高级空间工程的边界表达 |

先对比当前[公共Kit灰模](../../../art/models/central_court_kit_v01/README.md)的剪影与结构，再记录相似点、功能差异和需要修改的部件。环、悬浮、裂隙与错位本身均不能作为独占识别符；检查看的是它们如何被用于工程。

原版文件只作为本地研究入口。后续本机渲染或截图放在被Git忽略的`art/reference_library/`；可提交来源定位、分析与结论，不提交原版网格或未核实权利的图片。本轮没有复制原版几何、贴图或网络参考图，状态保持`visual_inspection_pending`。

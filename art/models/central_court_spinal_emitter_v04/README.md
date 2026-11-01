# 中庭级传承舰首：分段场约束阵面候选v04

2026-11-01，制作基线`4d4eeb3`。用户确认将舰首中轴两根长杆改为短宽分段约束模块、中央工作空腔和浅型前向发射阵面的方向；本批具体外观仍为`draft_pending_human_review`。这是公共中庭级F07舰首，不是爱缪莎个人旗舰或1.0之后的天体级战争机器。

## 本次变化

- 移除原中轴的两条长导轨、附属节点和底脊，共27个已知独立几何组件。
- 四组左右成对的短宽约束模块部分嵌入舰首，以低位横向承载桥支撑，中央保留开放工作段。
- 后部汇流座、四级整形工作面和前端一片宽浅阵面共同表达供能、约束、释放的顺序；本批只有静态结构与材质。
- `xl_gun_01`仍是唯一X槽发射点，位置与旋转同v03；四个`cc_field_stage_01..04`只预留视觉挂点，不增加武器槽或实际射击点。逐级充能动画尚未制作/接入。

普通舰首、中段、舰尾和造境平台均沿用原版本。整舰预览中的中段/舰尾只提供v03上下文，本批没有重新导出它们，也没有修改Mod运行资源。

## 预览与源文件

| 内容 | 文件 |
| --- | --- |
| 改前同镜头参考 | [v03整舰](previews/v03_reference.png) |
| 新舰首整舰效果 | [v04整舰](previews/ship_field_array.png) |
| 工作段近景 | [舰首近景](previews/field_array_closeup.png) |
| 可编辑源文件 | [Blender文件](central_court_spinal_emitter_v04.blend) |
| 导出与检查清单 | [emitter_manifest.json](emitter_manifest.json) |

三张预览均为Blender离线图；改前整舰参考复用v03已保存图，整舰镜头、灯光与材质处理相同。不能据此推断实际游戏曝光或战斗效果。

| 导出 | 三角面 | 定位器 | 材质 |
| --- | --- | --- | --- |
| `ccv04_bow_field` | 2720 | 1个真实发射点＋4个视觉挂点 | 1份共享材质 |
| `ccv04_bow_field_lod1` | 1360 | 同主网格 | 同主网格 |
| `ccv04_bow_field_lod2` | 624 | 同主网格 | 同主网格 |

两份简化网格是独立远景替代，尚未接引擎自动LOD切换。三张`cc_surface_v03_*` DDS按原文件复用：2048×1024、BC3/DXT5、12级mip；没有重新绘制或改变公共配色。源文件打包这三张DDS，无外部Blend库。

## 已检查与边界

三份PDX导出/回读、源文件保存后重开、单材质、UV范围及五个定位器保留通过。单一`xl_gun_01`与v03回读属性完全一致。主网格上两条中心射线分别核对工作段中轴与发射点前方；这不代表完整光束体积净空、游戏碰撞或实际射击已验收。清单中的开口宽度是设计名义值，局部护板与工作面会略微侵入。

[GFX](export/_central_court_emitter_v04.gfx)仅为三个作者空间网格的语法样品，不含运行entity。作者坐标仍为+Y舰首/+Z上方，接入前必须复用既有原生方向转换；不可直接覆盖当前v02。后续充能表现须单独连接实际武器效果，再集中做一次代表观察，不重做历史输入排障。

## 复现

只在独立后台factory-startup使用，不作用于用户交互场景：

```powershell
& 'G:\blender\blender.exe' --background --factory-startup --python-exit-code 1 --python tools/art/build_central_court_emitter_v04.py -- --pdx-addon-root 'C:\Users\Admin\AppData\Roaming\Blender Foundation\Blender\5.1\extensions\user_default'
```

需要本仓库v03源文件与`io_pdx_mesh`。本次未操作游戏、存档、另一屏幕或用户当前Blender场景。续接见[检查点](../../../reports/central_court_emitter_v04_checkpoint_2026-11-01.json)。

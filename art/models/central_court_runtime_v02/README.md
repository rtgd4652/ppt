# 中庭级与造境平台：v02开发候选接入

2026-11-01，基线`8e743e1`。`draft_integrated_runtime_pending`。本批把[作者空间候选](../central_court_surface_candidates_v02/README.md)转换并接入独立的Mod路径，正式外观与发布许可保持待确认。游戏显示结果见[本轮记录](../../../reports/central_court_v02_integration_2026-11-01.md)。

后续受控显示：运行态平台与传承炮击整舰已在4.5.2(04ef)的spawnentity场景中显示网格/材质；[平台画面](../../../reports/images/central_court_v02_platform_runtime_2026-11-01.png)、[整舰画面](../../../reports/images/central_court_v02_cruiser_runtime_2026-11-01.png)及[整舰结果](../../../reports/central_court_v02_ship_display_2026-11-01.md)保留。组合实体可以渲染；正常配装/造舰、轨道尺度、组件与效果仍待验。本段不改变具体外观与发布审核状态，也不把调试显示写成游戏船只/巨构获取。

## 已接入

- `mod/gfx/models/central_court_v02/`：7个主网格、3张共享BC3 DDS、GFX和独立实体包。14个远景替代仍保存在作者批次，尚未接入自动距离切换。
- 中庭级专用根实体`ccv02_strategic_cruiser_entity`，`part1/2/3`同原点挂接，4个原生命名目标点。根比例先取0.75，实际游戏尺度另验。
- 普通/传承舰首、炮击/航母中段、舰尾直接读取独立子实体；2个整舰预览实体只用于开发显示检查，没有新舰种或获取入口。
- 舰尾idle/moving接原生通用尾焰；根实体death接原生通用爆炸。没有复制原版媒体，模型也不借用旧Stage9舰体。
- 造境基址/运行态使用新实体，视觉偏移统一为`x=0,y=-25`，避免升级后沿用不同占位偏移。原生施工支架保留；选址、费用、工期、启用、普通殖民和维护保持。

## 修正的坐标问题

[只读原生对照](../../../reports/central_court_engine_space_2026-11-01.json)显示：原版舰首沿PDX负Z，候选作者空间的舰首导出后却沿正Z；原尾焰定位器还会指向竖直方向。导出转换只作用于独立后台内存中的副本：

1. 舰用网格和定位器位置绕作者Z轴转180度；建模源文件仍保留原来+Y舰首。
2. 炮位旋转与原版脊炮/炮塔定位器一致；尾焰与原版推进器旋转一致；两侧机库向各自舷外。
3. 以PDX实际回读检查正负轴和四元数，q/-q作为同一旋转；三段不再套用原版frame的分段骨架偏移。

原版数据仅记录边界、定位器与来源路径，没有把原版网格/纹理打包进项目。造境平台不是船体，不进行这次舰首方向翻转；星球参照球始终不导出。

## 来源与状态

[接入清单](integration_manifest.json)、[静态结果](../../../reports/central_court_v02_integration_validation_2026-11-01.json)。[资产登记](../../../docs/art/ASSET_REGISTRY.csv)新增7模型、3贴图及1实体包条目；全部为开发候选，外观/再分发状态保持待确认，不能将接入视为1.0正式美术完成。

实际gameplay脚本只更换entity与两阶段视觉偏移，其余可执行AST对比保持。作者Blend/PNG、旧灰模/概念和私人舰/枢纽均保留。LOD、实际炮塔/机库/推进方向、星球尺度与偏移、曝光、死亡效果和性能仍以游戏观察为准。

## 重建

先具备作者候选及原生坐标对照，再在独立后台运行：

```powershell
& 'G:\blender\blender.exe' --background --factory-startup --python-exit-code 1 --python tools/art/inspect_central_court_engine_space.py -- --pdx-addon-root 'C:\Users\Admin\AppData\Roaming\Blender Foundation\Blender\5.1\extensions\user_default'
& 'G:\blender\blender.exe' --background --factory-startup --python-exit-code 1 --python tools/art/integrate_central_court_v02.py -- --pdx-addon-root 'C:\Users\Admin\AppData\Roaming\Blender Foundation\Blender\5.1\extensions\user_default'
```

成功标记`CC_V02_INTEGRATION_OK`。转换脚本会更新本候选独立Mod目录；不在运行中的游戏上重建，也不修改用户Blender交互场景。费用/机制与显示引用的差异检查、运行状态和交接在阶段记录维护。

# 中庭级与造境平台：v04精修开发接入

后续材质更新：[v05可读性候选](../central_court_readability_v05/README.md)已更新运行目录中的七网格UV、三张新材质及GFX，实体/消费者名字仍为v04，几何/法线/全部定位器保持。本目录导出文件仍是旧v04不可变对照基线；下面的显示证据只对应当时版本。v05冷启动/载档通过，新实机外观未观察，详见[当前检查点](../../../reports/central_court_readability_v05_checkpoint_2026-11-01.json)。

2026-11-01，基线`ea9b5f6`。合并[v03整体精修](../central_court_surface_candidates_v03/README.md)的六个部件与[v04场约束舰首](../central_court_spinal_emitter_v04/README.md)，接入独立的`mod/gfx/models/central_court_v04/`。具体外观与再分发仍待确认，开发接入不代表1.0正式美术批准。最终运行结果见[本轮记录](../../../reports/central_court_v04_integration_2026-11-01.md)。

随后4.5.2(50ba)冷启动、reserve实际载入与代表整舰受控显示通过，[舰首近景](../../../reports/images/central_court_v04_bow_runtime_2026-11-01.png)和[完整视图](../../../reports/images/central_court_v04_ship_runtime_2026-11-01.png)已保存。当前光照下装甲偏暗，受光与材质暗部可读性待收敛；造境平台本轮未单独显示。运行状态以[检查点](../../../reports/central_court_v04_runtime_checkpoint_2026-11-01.json)为准，生成清单中的`game_display_verified=false`保留构建时事实。

## 交付

- 七个主网格、三张v03共享BC3/DXT5 DDS、网格GFX与十个实体定义；原v02运行资源与两份作者源文件保留。
- 中庭级根实体、五舰用区段与造境基址/运行态的八处消费者引用切换为v04；根比例0.75、同原点part1/2/3、四目标定位器、尾焰/死亡效果、巨构偏移保持v02接法。
- 传承舰首2720三角面、13个定位器：唯一`xl_gun_01`、四个`cc_field_stage`参考点、八个原生预充能粒子挂点。中段1576、舰尾2812，代表整舰合计7108三角面。
- 八个`xl_windup_1..8`按四组模块左右工作面分布，复用既有`tachyon_lance`的原生预充能接口；不增加炮位，不改武器数值，不新增周期事件。
- 简化网格保留在作者批次，本轮只安装LOD0，尚未接引擎自动距离切换。

## 原生充能接口

本机4.5.2的`gfx/projectiles/xl_weapons.txt`中，`tachyon_lance`的`windup_entity.invisible_extra_large_fixed`指向`tachyon_lance_windup_entity`。`gfx/models/combat_items/_xl_weapon_entities.asset`中已有四段时序：

| 时刻（原生实体秒） | 挂点 | 对应模块 |
| --- | --- | --- |
| 0.0 | `xl_windup_8/7` | 后部第一组 |
| 0.2 | `xl_windup_6/5` | 第二组 |
| 0.4 | `xl_windup_4/3` | 第三组 |
| 0.6 | `xl_windup_2/1` | 前部第四组 |

当前F07已引用该光矛，区段使用原生`invisible_extra_large_fixed`。本轮补齐上述挂点，沿用原生粒子/音效引用，不复制原版媒体，也未实现自制骨骼或材质亮度动画。挂点与代码接线已检查，实际战斗触发、循环、充能幅度和光束效果尚未观察，不能写成充能动画验收通过。

## 转换与检查

复用v02已验证坐标：舰用网格/定位器位置在后台内存中绕作者Z转180度，PDX舰首负Z、舰尾正Z；炮位朝向比对原版，推进器与原生一致、机库向外。巨构不做舰首翻转。唯一主炮位置/旋转与已安装v02的PDX回读完全一致；八个新增充能点位置亦经回读核对。

[接入清单](integration_manifest.json)及[静态检查](../../../reports/central_court_v04_integration_validation_2026-11-01.json)记录七网格回读、UV、材质、方向、资源引用及四份消费者非图形AST保持。既有舰种/F07/F08共14项检查和总静态通过。运行显示、正常配装/造舰、施工/轨道尺度与实际战斗仍按证据分别记录，不以静态通过代替。

## 复现

```powershell
& 'G:\blender\blender.exe' --background --factory-startup --python-exit-code 1 --python tools/art/integrate_central_court_v04.py -- --pdx-addon-root 'C:\Users\Admin\AppData\Roaming\Blender Foundation\Blender\5.1\extensions\user_default'
```

只使用独立后台进程，不保存/覆盖作者Blend或用户交互场景。脚本生成并安装独立目录；消费者引用与资产登记另随本次源码保存。旧v02资源不删除，未跟踪连续巨构原型不读取或纳入提交。只做一次代表游戏显示检查，不恢复历史help输入排障。

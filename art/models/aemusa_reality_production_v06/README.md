# 现实恒定旗舰与基线枢纽：离线生产候选v06

2026-11-01，基线`88071a1`，`draft_pending_human_review`，未安装。沿[五部件材质样品v0.2](../milestone4_surface_v02/README.md)与[既有外观方案](../../../docs/art/MILESTONE4_VISUAL_PROPOSAL.md)补齐生产格式，保留原轮廓和UV；不是一次完整造型重做，也不是最终美术。私人旗舰/危机基线枢纽与公共中庭级/F08造境平台保持独立身份。

| 部件 | 主网格三角面 | 简化替代1/2 | 原有挂点 |
| --- | --- | --- | --- |
| 旗舰舰首 | 368 | 184/84 | 2个L槽 |
| 旗舰中段 | 496 | 248/114 | 3个L槽 |
| 旗舰舰尾 | 504 | 252/114 | 1个L槽＋2推进 |
| 枢纽基址 | 364 | 182/82 | hub_center/build_point |
| 枢纽运行态 | 528 | 264/120 | 同基址位置/旋转 |

三张2048×1024 BC3共享DDS沿用v05校准材质，12级mip齐全；打包进[作者源文件](reality_production_v06.blend)。原v0.2源文件不修改。作者源仍为+Y舰首/+Z上方；`export/`中15份PDX已转换至原生方向，舰首负Z、舰尾正Z，枪位与推进旋转比对本机原版数据。位置/UV比较容差`1e-5`；法线因重新归一化出现约`1.5e-5`差异，采用`5e-5`容差并在清单记录最大误差。

源文件重开、五主网格几何/UV及接口对照、十五PDX回读/单材质、十份减面后的挂点保留、GFX及七实体样品语法检查通过。简化替代尚未接自动LOD，远景轮廓未作最终评审。原生尾焰/死亡效果只引用名称，未复制媒体，实际显示和比例未验；预览不附加原版炮塔，六个L槽仍保留。

## 预览

- [旗舰斜角](previews/flagship_oblique.png)、[旗舰侧视](previews/flagship_side.png)。
- [枢纽基址](previews/baseline_base.png)、[枢纽运行态](previews/baseline_active.png)。

两阶段用相同镜头和灯光。预览灯光/相机独立放在场景根，避免随舰段隐藏或被简化复制。以上均为Blender离线图，不代表游戏曝光；现有造型仍偏简化，细节与最终轮廓待收敛。

## 复现与接手

```powershell
& 'G:\blender\blender.exe' --background --factory-startup --python-exit-code 1 --python tools/art/build_reality_production_v06.py -- --pdx-addon-root 'C:\Users\Admin\AppData\Roaming\Blender Foundation\Blender\5.1\extensions\user_default'
```

仅独立后台，不触及用户Blender场景。原生方向只转换导出内存副本，作者源不反转。计划资源目录为`gfx/models/aemusa_reality_production_v06/`；本目录GFX/实体只是离线样品，没有更换当前Mod占位、唯一舰恢复或枢纽占领规则。实际接入时再更新ASSET登记，不将本包视为已安装。

[生产清单](production_manifest.json)、[检查点](../../../reports/reality_production_v06_checkpoint_2026-11-01.json)。本轮未操作游戏、存档或独立连续巨构原型。下一步按五部件方案收敛轮廓/细节，再合并一次接入和必要观察，不恢复旧输入/剧情测试。

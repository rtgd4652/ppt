# 中庭级与造境平台：材质可读性候选v05

后续实机确认：[新材质整舰已实际显示](../../../reports/central_court_readability_v05_confirmation_2026-11-01.md)，检修盖/分界/边缘反光的局部改善可见，主体仍暗；具体外观与正式曝光仍待收敛。下文原检查点的“显示未完成”保留为此前批次状态，不能覆盖这条新增证据。后续收尾工具调用中断，恢复时游戏进程已不在，原因未知，不重放已经提交的命令。

2026-11-01，制作基线`2125b28`，后续以`6230d1f`补实机确认。针对上一轮装甲偏暗，完成七个既有部件的材质校准和完整检修盖分区。已更新v04运行目录；源码、离线检查、冷启动、保留档载入及代表整舰显示通过，局部可读性改善可见。具体外观仍为`draft_pending_human_review`，没有正式曝光或发布批准。

## 本次调整

- 只读原版着色器和一例原版网格，并检查本Mod三段PDX：没有发现法线翻转，原深色装甲/面板约占九成三维表面积。这个比例不是屏幕面积，也不能单独证明实机光照问题的全部根因。
- 保留原RGB图集；Diffuse和Normal/DDS（含功能发光）与v03逐字节相同。装甲没有新增自发光。
- Properties按原生`G²×0.4`高光和`1-(1-B)²`金属度换算校准，降低涂层的金属度并补足柔和高光；数值见[材质清单](surface_manifest.json)。
- 只把完整、独立、位于上层两侧的薄检修盖从面板格移到既有雾银格。主承载体、舰桥和中央阵列保留原职责；不按单个三角面造成半块跳色。

| 代表区段 | 调整的完整部件数 | 雾银三维表面积调整前→后 |
| --- | --- | --- |
| 传承舰首 | 12 | 6.91%→22.57% |
| 炮击中段 | 20 | 2.74%→20.86% |
| 舰尾 | 12 | 4.81%→16.85% |

普通舰首、航母中段及造境两阶段同时沿用同一选取规则，细项见[构建清单](readability_manifest.json)。这些不是新部件或新增玩法。

## 预览与源文件

- [整舰离线预览](previews/ship_readability.png)、[舰首近景](previews/bow_readability.png)。
- [上一版同镜头整舰参考](../central_court_spinal_emitter_v04/previews/ship_field_array.png)。
- [可编辑Blender源文件](central_court_readability_v05.blend)，已打包三张DDS，保存后重开通过，无外部链接数据。

镜头、灯光与原v04离线条件相同，材质仍是Blender预览代理；不能把这些图当作新实机曝光通过。原作者源、旧v04导出基线和旧纹理保留，用户交互场景未改。

## 检查和运行边界

七份PDX逐三角形展开比较位置/法线，误差小于`1e-5`，全部定位器属性与旧v04相同。仍只有一个X槽发射点，四个场约束点和八个原生充能点保留；UV变化可能改变导出顶点拆分，三角面与实际几何保持。单材质、UV范围、三张2048×1024 BC3 DDS的12级mip、GFX和来源登记检查通过。总静态仍为272脚本/261事件/2271本地化，0错误/0警告；旧14项玩法检查复用，未重跑。

新进程4.5.2(50ba)已启动并载回reserve；显示命令输入10字符后被修饰键守卫停止，未回车。残留已清理，控制台/Debug View已关闭，游戏仍暂停2293.10.11，无新档或剧情变化。实机外观复查保留未完成，详见[检查点](../../../reports/central_court_readability_v05_checkpoint_2026-11-01.json)。不继续重试旧输入，不把这条命令留作接手队列。

## 复现与运行安装

```powershell
python -X utf8 -B tools/art/prepare_central_court_readability_v05.py
& 'G:\blender\blender.exe' --background --factory-startup --python-exit-code 1 --python tools/art/build_central_court_readability_v05.py -- --pdx-addon-root 'C:\Users\Admin\AppData\Roaming\Blender Foundation\Blender\5.1\extensions\user_default'
```

依赖复用现有隔离Pillow目录及io_pdx_mesh。只在独立后台执行；保存本批作者源后才转换导出副本。运行仍使用v04实体/消费者名称，只更新七个网格的UV、三张v05纹理和对应GFX；没有新实体、剧情条件、数值或周期脚本。正常舰船/巨构场景、充能战斗表现和自动LOD保持各自待验状态。

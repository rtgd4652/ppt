# 原画到游戏 UI 纹理

`prepare_ui_assets.py` 保留仓库原图，按固定裁切参数导出白夜馆事件背景和爱缪莎两种肖像。2026-09-26 使用 Python 3.14、Pillow 12.3.0 执行。

在仓库根目录运行：

```powershell
python -B tools/build/prepare_ui_assets.py
```

若 Pillow 安装在项目独立依赖目录，可用 `--pillow-dir temp/ui_build_deps` 指定。脚本不自动安装依赖。

| 输出 | 尺寸与用途 |
| --- | --- |
| `aemusa_white_night_pavilion_event.dds` | 450×150；白夜馆及主线事件图片 |
| `aemusa_portrait_ui.dds` | 575×380；基础肖像，主体限制为 210×350 |
| `aemusa_portrait_level_30_ui.dds` | 575×380；30 级肖像，主体限制为 210×350 |

输出使用 DXT5 保留透明留白，不修改原版 character 的全局缩放。脚本回读 DDS 核对尺寸和有效图像范围，并更新 `ui_assets_manifest.json` 中的源图／输出 SHA-256、裁切区域和主体范围；复核预览位于忽略目录 `temp/awp02-451-20260926/ui-previews/`。

构建成功只证明纹理可以导出及回读；事件背景、内阁、领袖详情和成长肖像仍须分别在游戏内检查。图标当前复用原版资源，专属图标制作仍由资产计划管理。

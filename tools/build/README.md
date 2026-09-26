# 原画到游戏 UI 纹理

`prepare_ui_assets.py` 保留仓库原图，按固定裁切参数导出白夜馆事件背景和爱缪莎两种肖像。2026-09-26 使用 Python 3.14、Pillow 12.3.0 执行。

肖像先用内置图像编辑工具去除场景背景，再由本脚本裁切、等比缩放和导出 DDS。透明 PNG、原图来源及完整提示词保存在 [`art/portraits/aemusa_ui/`](../../art/portraits/aemusa_ui/README.md)。构建时直接读取这些已保存的 PNG，不会再次生成或重画人物。白夜馆背景仍直接读取原画。

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

输出使用 DXT5 保留人物轮廓内外的透明通道，不修改原版 character 的全局缩放。脚本要求肖像裁切区域同时存在透明和不透明像素，防止误用带矩形背景的源图。脚本回读 DDS 核对尺寸和有效图像范围，并更新 `ui_assets_manifest.json` 中的源图／输出 SHA-256、裁切区域和主体范围；透明、浅底及深底预览位于忽略目录 `temp/awp02-451-20260926/ui-previews/`。

构建成功只证明纹理可以导出及回读；事件背景、内阁、领袖详情和成长肖像仍须分别在游戏内检查。图标当前复用原版资源，专属图标制作仍由资产计划管理。

2026-09-26 已在 4.5.1 冷启动中检查透明肖像的基础内阁、两种通讯、领袖列表和详情显示；30 级形态由独立超频测试档提供，不证明正常升级路径。具体证据与剩余验收见 [AWP-02 报告第 11 节](../../reports/aemusa_main_story_awp_02_validation_report.md)。

# 爱缪莎 UI 透明肖像

2026-09-26 按用户“截取人像去掉背景”的要求，使用 **内置 imagegen 图像编辑工具**生成两张透明 PNG，再用 Python / Pillow 按游戏规格裁切、缩放并导出 DXT5 DDS。未使用图像生成 CLI。

| 形态 | 原图（相对仓库根目录） | 透明衍生图 |
| --- | --- | --- |
| 基础 | `mod/gfx/models/portraits/aemusa_portrait_upper_dxt1.png` | `aemusa_base_cutout.png`，1659×948 RGBA |
| 30 级 | `mod/gfx/models/portraits/aemusa_portrait_level_30.png` | `aemusa_level_30_cutout.png`，993×1584 RGBA |

原图保留不变。衍生图含真实 alpha；基础形态去除城市、天空等背景，30 级形态去除晶体场景、王座和悬浮卡牌。生成式编辑可能改变局部线条细节，不能当作逐像素无损抠图；30 级衍生图还重新居中放大了人物，因此有独立裁切参数。

游戏采用头部及躯干的窄幅取景，画布为 575×380，主体不超过 210×350，保持原图比例以适配通讯左栏。它不是完整全身立绘。导出配置及 SHA-256 见 [`ui_assets_manifest.json`](../../../tools/build/ui_assets_manifest.json)，重建方法见 [`tools/build/README.md`](../../../tools/build/README.md)。

## 基础肖像完整提示词

```text
Use case: background-extraction. Asset type: transparent character portrait cutout for an existing Stellaris mod. This attached local image is the edit target. Remove the entire city, sky, buildings, distant lights and atmospheric streaks, leaving only the existing anime woman: her exact face and expression, blonde ponytail and loose hair, black and red feather hair ornament, earrings, neck ornament, black and magenta dress, rose, visible arms and gloved hands, and the tarot card held by her left hand. Preserve the original drawing, identity, proportions, pose, colors and details as faithfully as possible. Do not redraw, beautify, add limbs or invent the cropped lower body. Preserve the existing landscape composition, positioning, scale and crop. Transparent alpha background, including genuine transparent negative space between her arms, fingers and hair; no checkerboard pattern painted into the image, no solid background, no drop shadow, no extra glow or text. Clean fine hair and feather edges without a background-color halo. Return a single RGBA PNG cutout.
```

## 30 级肖像完整提示词

```text
Use case: background-extraction. Asset type: transparent level-30 character portrait cutout for an existing Stellaris mod. The attached local image is the edit target. Extract only the seated anime woman from this exact illustration. Remove all crystalline architecture, throne including its back and armrests, floor, chains, floating tarot cards and detached magic light trails. Keep the exact existing woman: face, red eyes and expression, blonde hair, blue-jeweled crown and hair ornament, dark-blue and black flower dress, lace and fabric details, sheer sleeves, gloves, visible arms and hands, legs and boots. Preserve her identity, original drawing style, original pose, proportions, colors, original placement and scale within the tall canvas. Do not redraw or redesign the woman; do not invent new body parts; no extra ornaments, text, props or glow. Produce real transparent alpha behind and between her hair, limbs and dress edges, preserving fine edges and natural translucency where appropriate. No background-colored fringe, no solid color background, no painted checkerboard and no drop shadow. Return one clean RGBA PNG cutout.
```

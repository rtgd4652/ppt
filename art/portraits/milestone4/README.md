# 里程碑4神器使透明肖像

日期：2026-10-08。首批为安托涅瓦、晏华、拉比／阿米特。生成方式：内置 `image_gen`，`transparent_background=true`；后处理使用用户已选择的 Python 等比裁切、缩放、DXT5 导出。没有使用 CLI/API fallback。

## 原画与衍生关系

- 安托涅瓦：原图 `art/reference_library/original_game/antoniva/antoniva_base.png` → `antoniva_base_cutout_v01.png` → `mod/gfx/models/portraits/antoniva_portrait_ui.dds`。去背景和页脚，保留基础形态、方舟与服饰；UI只取人物上部及方舟局部。
- 晏华：原图 `art/reference_library/original_game/yanhua_character_color_review/「神之头脑」晏华 Char Illustration Cut.png` 本身带透明调色板通道 → RGBA `yanhua_base_cutout.png` → `mod/gfx/models/portraits/yanhua_portrait_ui.dds`。没有再次生成或重画。
- 拉比／阿米特：原图 `art/reference_library/original_game/rabi_character_color_review/拉比-地精.png` → `rabi_amit_base_cutout_v01.png` → 双主体取景 `rabi_amit_joint_portrait_v03.png` → `mod/gfx/models/portraits/rabi_amit_portrait_ui.dds`。v02遗漏阿米特头部，弃用且不进入mod；v03保留孩子与阿米特的装甲头部，属于生成式重新取景样品。

构建：`python -X utf8 -B tools/build/prepare_companion_portraits.py --pillow-dir temp/ui_build_deps`。输入／裁切／尺寸／透明往返信息见 [build_manifest.json](build_manifest.json)。不计算例行哈希。预览见 [三人深浅底对照](previews/three_portraits_contact_sheet.png)。DDS为575×380、DXT5，主体不超过210×350，沿用爱缪莎画布与底部对齐方式。

来源缓存不直接进入发布包；本批衍生纹理的来源与再分发状态仍为 `source_review_required` / `pending`。现有批准角色锚点不等于本批画面或发布权限已经批准。运行显示结论另见本日报告，构建脚本只确认文件规格。

## 其余六人（2026-10-08）

安、赛斯、幽桐、格蕾莎、雯梓使用素材本身的透明调色板通道，转换为 RGBA 后导出；没有再次生成或重画。丽使用内置 `image_gen` 去背景，再按人物上部取景；生成式提取可能改变细小边缘，画面审阅与发布权限仍待确认。

| 人物 | 原图（均在 `art/reference_library/original_game/`） | 本目录透明源 |
|---|---|---|
| 安 | `an_character_color_review/「光荣女仆」安 Char Illustration Cut.png` | `an_base_cutout.png` |
| 赛斯 | `seth_character_color_review/「神官」赛斯 Char Illustration Cut.png` | `seth_base_cutout.png` |
| 幽桐 | `yutong_character_color_review/「诛心」幽桐 Char Illustration Cut.png` | `yutong_base_cutout.png` |
| 格蕾莎 | `greysa_character_color_review/「白医」格蕾莎 Char Illustration Cut.png` | `greysa_base_cutout.png` |
| 雯梓 | `wenzi_character_color_review/wenzi_base_cut.png` | `wenzi_base_cutout.png` |
| 丽 | `li_character_color_review/li_base_full.png` | `li_base_cutout_v01.png` |

六人分批构建命令：`python -X utf8 -B tools/build/prepare_companion_portraits.py --pillow-dir temp/ui_build_deps --roles an seth yutong greysa wenzi li`。该参数保留首批三人的纹理与记录；不带 `--roles` 可重建九人，爱缪莎沿用既有肖像。六人预览见 [深浅底对照](previews/6_portraits_contact_sheet.png)，规格和裁切见构建清单。仅刷新已存在的唯一人物，不创建替代领袖。

六人正常核心通讯和统一新档读回已通过；当前九张新增肖像连同爱缪莎既有资源均已接通。实际运行范围见[六人补齐记录](../../../reports/milestone4_remaining_portraits_2026-10-08.md)，构建清单不代替游戏证据或外观批准。

### 丽去背景完整提示词

```text
Edit this provided official character illustration only by separating the illustrated character Li and her physical closed golden-and-black spiral umbrella weapon from the plain pale gray background. Produce a clean transparent-background cutout of the same character and weapon, preserving the exact pose, face, eyes, blonde high side ponytail, black hair bow, yellow and dark brown-black segmented outfit, rounded puff sleeves, skirt and gray-purple leg layers, drawn linework and original colors. Preserve every visible physical part and the complete visible silhouette. Keep the original appearance and proportions; do not restyle, redesign, add parts or redraw the character. Remove the pale gray background and detached atmospheric background glows, specks and arcs. The empty footer and game logo are outside the character silhouette and should not be included in the cutout. Retain physical hair strands, umbrella structure and costume edges with clean soft antialiasing and transparent holes between them. This is the base-form portrait, no awakening changes, no gold-only recoloring, no new sci-fi costume. Return transparent RGBA PNG with adequate transparent margins.
```

## 首批完整提示词

### 安托涅瓦去背景

```text
Use case: background-extraction. Edit the supplied base-form Antoniva illustration only. Remove the entire pale grey studio background and exclude the printed title/footer from this portrait cutout. Return the subject on a genuinely transparent alpha background. Preserve the exact character identity, original face and amber eyes, very long dark warm-brown hair, calm seated pose, lavender-grey/pink and warm white layered wide sleeves, black-purple inner clothes, cloth detail, and the original Noah's Ark directly supporting her with dark hull and restrained warm-gold wing structures. Keep the original drawing and material colors intact; do not redraw the face, redesign the outfit, add awakening wings, blue-white uniforms or cosmic decorations. Retain clean complete edges and enough margin for later deterministic crop/resize. No text, no replacement backdrop, no shadows outside the actual subject. This is a project-local developmental portrait derivation; do not add any approval or publication label.
```

### 拉比与阿米特完整去背景v01

```text
Use case: background-extraction. Edit this base-form Rabi and Amit illustration only. Remove the pale grey background, the large empty border and the printed footer region, returning the original Rabi-and-Amit artwork with genuine transparent alpha. Preserve BOTH subjects together, the exact youthful boy identity and face, grey-beige short tousled hair with upward tips, amber eyes, crescent hair ornament, loose warm orange/yellow jacket, grey-green knit inner layer, dark shorts, white knee socks and original non-sexual playful pose. Preserve Amit's complete protective head, visible claws, shell geometry, carbon-black/sandstone-grey armor and warm amber seams, and its relationship directly supporting/protecting the boy. Keep original colors, drawing style and material definition; do not mechanize Amit or redesign either character, do not add saddle, reins, new clothing, awakening features, a personless monster image, or a boy-only image. Keep their original shared pose and spatial relationship. No text, no replacement scene, no glow beyond existing subject edges. Leave enough margin to crop deterministically into a compact joint UI portrait later.
```

### 拉比与阿米特共同取景v03

```text
Use case: precise-object-edit. This source has TWO equally important characters: the small boy Rabi at the center and the enormous protective monster Amit whose HEAD is at the RIGHT (the angular sandstone armored face with orange/amber seams and tall black horn tips). Make a tight 2:3 vertical transparent UI portrait showing BOTH Rabi's head and upper body AND Amit's recognizable RIGHT-HAND HEAD. Place Rabi in the upper left foreground, Amit's original armored HEAD immediately below and to his right as a close protective pair. Omit or crop the remote tail on the left, the bottom legs and most huge body. Do not substitute the tail or shoulder for the monster's head: Amit's actual angular armored face from the right of the source MUST remain visibly present in the lower half. Preserve the source drawing and exact faces, boy age, hair, crescent ornament, amber eyes, orange jacket, green-grey knit, Amit's angular armor, warm amber seams and original horn silhouette. No redesign, new outfit, adultization, saddle or cockpit. Transparent background, no text. Both heads are the subject, use most of the vertical canvas, clean antialiased alpha edges without red/yellow external fringe or haze. One coherent paired portrait, not a contact sheet.
```

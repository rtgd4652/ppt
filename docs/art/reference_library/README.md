# 《神器使》Mod 视觉参考图库

本目录用于维护经过登记、筛选与分析的视觉依据。它帮助角色立绘、舰船、建筑、区划、巨构、UI、图标和粒子特效共享稳定的判断标准，但不等同于正式游戏资产库。

## 核心边界

- 参考条目只说明“可以学习什么”，不自动授予复制、改编、提交或再分发权限。
- 正式资产位于 `assets/` 的生产流程目录或 `mod/gfx/` 运行时目录，并由 `docs/art/ASSET_REGISTRY.csv` 单独登记。
- 原作截图、网络图片及授权不明确素材可以下载到 `art/reference_library/`，但该目录由 `.gitignore` 排除。
- Git 中只保存来源定位、权利状态、视觉分析、Moodboard 和审核结论。
- `unknown` 不能自动改成 `licensed`；没有明确许可时，默认只允许本地分析。

## 目录

```text
docs/art/reference_library/
├── README.md
├── EXISTING_RESOURCE_AUDIT.md
├── REFERENCE_INDEX.md
├── REFERENCE_MANIFEST.csv
├── SOURCE_AND_RIGHTS.md
├── ANTI_REFERENCES.md
├── original_game/
├── stellaris/
├── external/
└── moodboards/
```

跨类别的项目自制校准板位于：

```text
docs/art/calibration/
├── CENTRAL_COURT_MATERIAL_CALIBRATION.md
├── central_court_material_calibration.svg
├── BLACK_GATE_OTHERWORLD_COMPARISON.md
└── black_gate_otherworld_comparison.svg
```

这些文件用于分析、校色和审核，不是可直接导入 `mod/gfx` 的正式资产。

本地二进制缓存位于：

```text
art/reference_library/
```

## 工作流

1. 在 `REFERENCE_MANIFEST.csv` 建立唯一 `reference_id`。
2. 填写来源、版权或许可状态、允许用途与待学习内容。
3. 如需本地副本，将未获明确再分发许可的文件放入 `art/reference_library/`。
4. 完成人工审核后，将条目设为 `reviewed`、`approved_anchor`、`supporting`、`rejected` 或 `source_uncertain`。
5. Moodboard 只能引用已经登记或明确标注为“待建立”的 ID，并必须写出结论与禁止项。
6. 制作正式资产时，只提取已批准的抽象规律，或使用项目原创／明确授权素材。
7. 正式资产进入 `mod/gfx`、`textures` 或 `models` 前，在 `docs/art/ASSET_REGISTRY.csv` 重新登记来源链和审核状态。

## 生成索引

```powershell
python tools/art/build_reference_index.py
```

该工具只离线读取 CSV：

- 检查重复 ID、必填字段、枚举、来源与本地路径。
- 按分类生成 `REFERENCE_INDEX.md`。
- 对来源不明、授权待确认和未审核条目标记警告。
- 不联网、不下载、不修改原图、不复制二进制文件。

严格检查可使用：

```powershell
python tools/art/build_reference_index.py --check --strict
```

当前清单刻意保留若干 `planned_reference_slot`。它们是可见的资料缺口，不是可使用素材；只有补齐具体来源和权利状态后才可升级。

## 参考与正式资产的转换门槛

转换前必须确认：

- 是否原创重绘或重新建模。
- 是否只提取抽象的结构、色彩、材质、构图或动态规律。
- 是否拥有使用与再分发权限。
- 是否通过项目美术审核。
- 是否满足 Stellaris 的尺寸、DDS、模型、LOD、定位器和性能要求。

任何一项未确认，都不得把参考图直接复制进正式资产目录。

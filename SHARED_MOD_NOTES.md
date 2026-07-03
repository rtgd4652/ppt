# 神器使 Mod 共享说明

## 武器数值写法

- 结论：`common/component_templates/*.csv` 当前无法被 Stellaris 正常读取为舰船武器数值来源。
- 处理规则：所有神器使舰船武器的基础数值必须直接写在对应 `.txt` 的 `weapon_component_template` 里。
- 必填字段：`damage`、`windup`、`total_fire_time`、`power`、`range`、`accuracy`、`tracking`，以及需要的 `hull_damage`、`shield_damage`、`armor_damage`、穿透字段。
- 不要再依赖 CSV 提供伤害、射程、冷却或命中数据；否则船坞 UI 可能显示 `1-1` 伤害、`0-0` 射程或其他默认值。

## 当前执行状态

- `common/component_templates/aemusa_artifact_components.txt` 中旧的 S/M/L 命运塔罗射线已补齐 TXT 内联武器数值。
- `common/component_templates/aemusa_artifact_tiered_components.txt` 中新增的分级武器已全部使用 TXT 内联数值。
- `common/component_templates/aemusa_weapon_components.csv` 仅作为旧数据残留参考，不再作为有效加载来源。
- `assets/icon_generation/generate_artifact_icons.py` 已生成 90 个神器使专属 PNG/DDS 图标，并写入 `interface/aemusa_generated_icons.gfx` 与 `interface/aemusa_progression_icons.gfx`。
- 科技、建筑、区划、陆军、飞升、传统、法令、决议、起源、舰船部件和部件组已改用专属图标引用。

## 平衡曲线

- 前期：数值平庸，只提供神器使风格和轻微优势。
- 中期：约等于原版后期水平。
- 后期：明显超模，但用高合金、高能量、稀有资源和小文物成本约束规模。

## 科技与飞升分线

- 爱缪莎个人线：`ap_artifact_court_destiny` 是入口；该飞升要求爱缪莎存在并达到 30 级，同时完成中央庭守望传统和至少 3 个已选飞升。
- 爱缪莎科技线：塔罗、黑门、中央庭、七日、命运观测塔、命运之主等科技均要求 `ap_artifact_court_destiny`，不得再由召唤法令直接赠送。
- 神器使物种线：`ap_artifact_user_resonance_path` 是一段飞升，`ap_artifact_user_apotheosis_path` 是二段飞升；这条线不依赖爱缪莎飞升。
- 神器使军备科技：`tech_artifact_user_combat_doctrine` 只依赖原版基础军科；`tech_artifact_user_resonance_armaments` 要求一段物种飞升；`tech_artifact_user_apotheosis_warfare` 要求二段物种飞升。
- 命名约束：神器使陆军与常规舰船分级武器/组件的玩家可见名称使用“神器使、神器共鸣、神器终解”风格，避免混入爱缪莎个人线的塔罗、黑门、命运主宰等命名。

## 图片与图标补全规则

- 缺少事件图、领袖图、舰船预览、建筑图标或部件图标时，优先前往永远的七日之都灰机 wiki（`https://f7d.huijiwiki.com/wiki/首页`）检索角色、神器、白夜馆、中央庭、黑门、影装等题材参考。
- 若 wiki 或相关公开资料中存在适合当前对象的参考图，只将其作为题材、构图、配色和元素参考，再用自带绘图工具生成原创图；不要直接把网页图片原样放入模组资源。
- 若没有合适参考，则按七日之都的都市科幻、日常与灾厄并存、青绿色 UI 光效、神器纹样、塔罗/契约/黑门意象、白夜馆和中央庭气质设计原创图。
- 图标优先保持 Stellaris 可读性：小尺寸高对比、轮廓清晰、少文字、主体居中；神器使专属图标可使用青绿、紫、金、黑的组合，但避免整套资源变成单一色调。
- 后续缺失图标优先追加到 `assets/icon_generation/generate_artifact_icons.py` 的 `ICONS` 表，再重新运行生成器和引用更新脚本，避免手工散落创建。
- 本模组是免费公开项目，不以盈利为目的；即便如此，新增资产仍优先采用“参考后原创生成”的流程，减少直接搬运造成的授权和维护风险。

## 开发约束

- 纯新增优先，不覆盖原版对象。
- 所有新增脚本注释使用中文。
- 不修改领袖事件主线。
- 不修改舰船模型、船体段和舰船部件保存问题相关文件。

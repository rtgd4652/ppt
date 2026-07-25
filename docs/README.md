# README

## 项目介绍

《神器使》Stellaris Mod 将《永远的七日之都》的神器使、中央庭、黑门和灾后文明主题转化为 Stellaris 4.4.3 的文明与领袖内容。

当前可玩原型基线为 `0.1.0`；对外目标是完整大型 `1.0`。所有 `v0.x` 仅作为内部开发里程碑，不代表彼此割裂的公开叙事版本。

当前已接入：

- 神器使物种、特质、起源、专属星球和预设帝国。
- 白夜馆功能入口。
- 爱缪莎、赛斯、幽桐、拉比四名领袖。
- 专属飞升、传统、科技、建筑、岗位和区划。
- 已废弃命运观测塔旧案的脚本遗留与等待重新归类的旧 Stage 9 技术样舰。

白夜馆仅负责招募、联络、档案展示与管理，不属于世界观组织。

1.0 已锁定十名神器使：安托涅瓦、爱缪莎、晏华、安、赛斯、幽桐、拉比、格蕾莎、雯梓、里见茜。冈部伦太郎可以按神器使规则设计，但当前作为可追加联动成员，不占这十个锁定名额；司篁暂不加入 1.0 基线。

当前权威入口：

- `knowledge/characters/character_roster_v1.0.md`
- `knowledge/characters/status/README.md`
- `docs/design/v1.0_narrative_constraints.md`

## 安装方法

Stellaris 启动器应加载仓库中的 `mod/` 目录，而不是仓库根目录：

```text
C:\Users\Admin\Desktop\ppt\simple_leader_edict\mod
```

1. 在启动器中创建或编辑本地 Mod。
2. 将注册文件的 `path` 指向上述目录。
3. 在播放集中只启用本 Mod 进行封版测试。
4. 确认 `mod/descriptor.mod` 被正确读取。

## 依赖

- Stellaris 4.4.*，脚本目标版本为 4.4.3。
- Git，用于版本管理。
- Blender 与 PDX Mesh 插件，仅在继续开发模型时需要。
- Node.js 与 Playwright，仅在运行知识库采集工具时需要。

开发约定：

- 所有项目会话必须在北京时间 23:00 前结束并保存进度；23:00 是完成截止时间，不是开始收尾时间。
- 最迟在 22:30 前进入收尾，复杂任务应更早预留验证、中文提交和状态回报时间。
- 详细共享代理规则见仓库根目录 `AGENTS.md`。
- Stellaris 脚本继续添加中文注释。
- Git 提交信息使用中文。
- `.txt`、`.gfx`、`.asset`、`.gui` 使用 UTF-8 无 BOM。
- 简体中文本地化 `.yml` 保留 UTF-8 BOM。
- 不覆盖原版文件。

## 路线图

- 内部基线：保留现有四名可玩领袖与文明系统，完成回归测试。
- 1.0 角色闭环：补齐十名神器使资料、标准档案、白夜馆接入、立绘、本地化和测试。
- 1.0 主线闭环：完成爱缪莎从有限观测到“命运主宰”的完整路线。
- 美术与模型：按 Art Bible 重新设计爱缪莎专属舰与命运类巨构；旧 Stage 9 舰体改作其他舰船。

详细内容见 `docs/ROADMAP.md`。

## 本地知识库

当前知识重建工作线独立于 Mod 功能开发，使用 Markdown + 本地 SQLite 索引的双层结构：

- 知识库总索引：`knowledge/README.md`
- 工作说明：`docs/project/knowledge_rebuild_v0.1.md`
- 人工确认层：`knowledge/curated/README.md`
- 数据库说明：`knowledge/database/README.md`
- 工具说明：`tools/knowledge/README.md`

当前世界观基础文档包括事实／正史／谜团矩阵、灾后至星际时代详细时间线、中央庭国家制度圣经和宇宙论圣经；推荐从 `knowledge/README.md` 按顺序阅读。进入任何 1.0 剧情或角色实现前，必须再阅读 `docs/design/v1.0_narrative_constraints.md`。

当前已索引 85 集视频目录，以及 47 个灰机 Wiki 主线剧情页面、129 棵剧情选择树和七名角色来源。已完成《正轨的箱庭》《无垢的人偶》《避世的方舟》《深渊的步伐》四条早期主线的逐页采集；Wiki 文本是当前剧情正文主来源，视频只作为人工审核后的补充叙事证据。

## 视觉参考图库

视觉参考图库位于 `docs/art/reference_library/`，用于统一角色、舰船、建筑、区划、巨构、UI、图标和粒子特效的判断标准。

- 参考登记：`docs/art/reference_library/REFERENCE_MANIFEST.csv`
- 自动索引：`docs/art/reference_library/REFERENCE_INDEX.md`
- 来源与权利边界：`docs/art/reference_library/SOURCE_AND_RIGHTS.md`
- 反面参考：`docs/art/reference_library/ANTI_REFERENCES.md`
- Moodboard：`docs/art/reference_library/moodboards/`
- 正式资产登记：`docs/art/ASSET_REGISTRY.csv`

来源或再分发状态不明的图片只保存在被 Git 忽略的 `art/reference_library/`，不得直接复制进正式 Mod 资产目录。

## 截图

游戏截图和开发参考分别存入：

- `assets/ai_generated/`
- `assets/ui/`
- `assets/icon/`
- `assets/portrait/`
- `assets/official_reference/`

官方参考和开发源图不直接进入最终 Mod 发布目录。

## 开发计划

当前阶段只允许封版修复，不增加角色、剧情、舰船武器槽或正式图标。

封版流程：

1. 完成脚本与编码静态检查。
2. 使用新开局完成十二项手动测试。
3. 检查最新 `error.log`。
4. 回写测试报告。
5. 快进合并到 `main`。
6. 创建并推送 `v0.1.0` 标签。

相关文档：

- `docs/PROJECT_STATUS.md`
- `docs/project/project_status_v0.1.md`
- `docs/project/v0.1_release_freeze.md`
- `reports/v0.1_test_report.md`
- `reports/v0.1_manual_test_checklist.md`

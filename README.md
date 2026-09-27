# SevenDays_Mod · 神器使

《永远的七日之都》主题 Stellaris Mod，当前开发与运行验证目标为 Stellaris 4.5.1，对外目标为完整 1.0。描述文件仍保留原型的 `4.4.*` 声明，尚未完成全 Mod 的 4.5.1 兼容验收。

仓库保留文明系统与四名领袖的可玩原型。1.0 背景准备、角色基础设计和主线设计已进入批准后的分包实现阶段。AWP-02（序章至第三章）已通过运行验收；当前推进 AWP-03（第四至第六章及失落帝国战争），已核对受控战争和章节正常路径，剩余反例与自然战争仍待验证。

`mod/descriptor.mod` 中的 `0.1.0` 是现有原型标识，不表示当前工作区已经冻结或发布。内部里程碑和正式发布按下列当前文档管理，不自动沿用历史标签发布流程。

## 新会话入口

1. [当前进度](docs/PROJECT_STATUS.md)：当前工作包、完成层级、阻塞和下一步。
2. [主线工作包](docs/design/aemusa_main_story_implementation_work_packages_v1.0.md)：范围、依赖与逐包授权记录。
3. [AWP-03 运行记录](reports/aemusa_main_story_awp_03_runtime_2026-09-27.md)：当前 `runtime_status: in_progress`。
4. [AWP-02 运行验收记录](reports/aemusa_main_story_awp_02_validation_report.md)：T001～T004 已通过，20/20 个事件簇完成后三次重开已核验。

需要理解整体设计时再阅读 [架构](docs/ARCHITECTURE.md)、[路线图](docs/ROADMAP.md)、[执行清单](docs/TODO.md) 和 [文档索引](docs/README.md)。共享规范见 [AGENTS.md](AGENTS.md)。

## 目录职责

| 目录 | 职责 |
| --- | --- |
| `raw/`、`indexes/` | 来源原文及页面、图片索引 |
| `knowledge/` | 人工审核资料、项目正史、角色档案及可重建数据库 |
| `docs/` | 叙事、机制、美术约束与当前计划 |
| `mod/` | Stellaris 唯一加载目录 |
| `assets/`、`art/` | 制作源文件与参考材料 |
| `tools/` | 采集、转换、构建与检查工具 |
| `reports/` | 实施、静态检查、运行测试的证据 |

## 加载与检查

Stellaris 启动器应加载本仓库的 `mod/`，不要加载仓库根目录。当前本地路径：

```text
C:\Users\Admin\Desktop\ppt\simple_leader_edict\mod
```

在仓库根目录运行以下只读静态检查，无需安装第三方 Python 包：

```powershell
python -B tools/validation/check_mod.py
```

静态通过不等于游戏内验收通过。检查范围、工具测试和工作区快照见 [检查工具说明](tools/validation/README.md)。

## 已锁定边界

- 白夜馆只承担招募、联络、档案与管理入口，不是世界观势力。
- 1.0 十名神器使范围见 [角色名册](knowledge/characters/character_roster_v1.0.md)，不因计划整理扩张。
- 旧 Stage 9 舰体与旧命运观测塔属于遗留原型，不是正式终局资产。
- 角色、美术、主线和运行验收分别记录状态，不以资料批准代替游戏完成。
- 不覆盖原版文件；新代码使用中文注释；提交信息使用中文。
- 非本地化脚本使用 UTF-8 无 BOM，简体中文本地化保留 UTF-8 BOM。
- 每次会话遵守北京时间 23:00 前结束、最迟 22:30 收尾的共享规则。

## 知识与资产

[知识库入口](knowledge/README.md)说明原作事实、项目正史和开放谜团的层级；SQLite 仅为可重建索引，不替代 Markdown、JSON 与原始来源。[资产生产清单](docs/art/ASSET_PRODUCTION_PLAN.md)安排实际制作需求；参考材料不直接作为正式发布资产。

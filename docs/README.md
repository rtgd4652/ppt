# README

## 项目介绍

《神器使》Stellaris Mod 将《永远的七日之都》的神器使、中央庭、黑门和灾后文明主题转化为 Stellaris 4.4.3 的文明与领袖内容。

当前候选版本为 `0.1.0`，定位是“神器使文明基础系统 + 白夜馆首批角色 + 第一版终局内容”的稳定基线。

当前已接入：

- 神器使物种、特质、起源、专属星球和预设帝国。
- 白夜馆功能入口。
- 爱缪莎、赛斯、幽桐、拉比四名领袖。
- 专属飞升、传统、科技、建筑、岗位和区划。
- 命运观测塔脚本与命运之主基础舰体。

白夜馆仅负责招募、联络、档案展示与管理，不属于世界观组织。

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
- Node.js，仅运行静态验证工具时需要；验证工具不需要 Playwright。

开发约定：

- Stellaris 脚本继续添加中文注释。
- Git 提交信息使用中文。
- `.txt`、`.gfx`、`.asset`、`.gui` 使用 UTF-8 无 BOM。
- 简体中文本地化 `.yml` 保留 UTF-8 BOM。
- 不覆盖原版文件。

## 路线图

- v0.1.0：完成静态清错、游戏内复测和首个稳定标签。
- v0.2：实装安托涅瓦、晏华，并建立中央庭核心人物框架。
- v0.3：确定统一美术规范，补齐图标，继续完成舰船和巨构模型。

详细内容见 `docs/ROADMAP.md`。

## 架构

v0.2 开始采用“运行目录保持扁平、文件名前缀表达模块归属”的架构，避免依赖 Stellaris 对深层目录的递归加载行为。

架构文档入口：

- `docs/architecture/README.md`
- `docs/architecture/runtime_architecture_v0.2.md`
- `docs/architecture/naming_and_compatibility.md`
- `docs/architecture/migration_plan_v0.2.md`
- `docs/architecture/branch_release_workflow.md`

静态验证入口：

```powershell
node tools/build/validation/validate-mod.js
```

当前缺失图标按既定决策暂缓补齐，默认验证只警告；统一美术规范确定后再启用 `--strict-art`。

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

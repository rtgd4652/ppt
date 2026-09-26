# 正式 Mod 检查与工作区快照

使用 Python 3.10 或更新版本的标准库；不需要安装第三方依赖。命令从仓库根目录执行。

## 只读静态检查

```powershell
python -B tools/validation/check_mod.py
python -B tools/validation/check_mod.py --json
```

默认扫描正式 `mod/`，不扫描隔离原型、开发源图或缓存。退出码 0 表示已覆盖的静态检查通过；1 表示存在错误。命令只向终端输出，不自动修改文件或报告。

覆盖范围：

- UTF-8、非本地化无 BOM、本地化 BOM 与重复 key。
- 花括号、引号、注释、块结构与赋值结构。
- 项目事件 ID／namespace、项目内部事件引用和事件中文本地化。
- 主线 scripted trigger／effect 调用是否有定义。
- 状态登记唯一性、直接状态引用、直接读写类型以及禁止直接写入保留枚举。
- 显式项目资源路径、模型同目录纹理、事件图片 sprite 注册。

若需要检查原版显式图片路径，可传入本机游戏目录：

```powershell
python -B tools/validation/check_mod.py --game-dir '实际的 Stellaris 安装目录'
```

未指定时，原版路径标记为未验证，不误报为项目资源缺失。原版脚本语义、作用域、效果合法性、参数化接口的实际写入语义、事件可达性、引擎隐式图标、UI 曝光、存档恢复和玩法平衡仍需原版文件核对与运行测试。静态通过不能将 `runtime_status` 改为通过，也不代表既有 41 项美术缺口消失。

## 工具回归测试

```powershell
python -B -m unittest discover -s tools/validation/tests -v
```

检查器测试在系统临时目录建立小型输入，覆盖重复与缺失引用、编码、状态写入边界、字符串／颜色块、原版路径判定、只读性及快照完整性，不修改正式 Mod。

`test_awp02_state.py` 另外读取正式 AWP-02 事件、入口条件和生命周期接口，用有限的脚本账本执行器检查 192 组选择组合、旧窗口重复选择、延迟事件重复排队、冲突状态和绕过外层 trigger 的强制跳章。它不加载游戏，只提供玩家国家、领袖存在和银河参与等外部前置；不验证真实调查／殖民回调、30 天计时、UI 或存档恢复。遇到未支持的脚本条件／效果直接失败，不静默忽略。

## 保存工作区快照

```powershell
python -B tools/validation/snapshot_workspace.py --output temp/checkpoints/本次测试前.zip
```

输出 ZIP 包含：

- `manifest.json`：基准提交、分支、时间、文件 SHA-256 与删除清单。
- `tracked.patch`：相对 HEAD 的已跟踪文件二进制补丁。
- `files/`：当前变更文件及未跟踪文件的原始字节，包括中文／空格路径。

写入后校验 CRC 与文件哈希；已有快照拒绝覆盖。不修改 Git 索引、分支、提交或运行文件。不包含被 Git 忽略的数据库、缓存和参考素材，也不保存索引与工作区原来的分期差别。

恢复时需要清单记录的 `base_commit`。先在独立可丢弃检出中核对清单与哈希，再应用原始文件和删除清单，禁止直接覆盖正在工作的目录。快照不是独立发布包，也不能替代正式中文提交。测试报告同时记录 HEAD 和快照位置，避免把未提交的运行结果错误归给 HEAD。

## 当前项目入口

[项目状态](../../docs/PROJECT_STATUS.md)、[架构](../../docs/ARCHITECTURE.md)、[本轮验证报告](../../reports/project_architecture_review_2026-09-26.md)。

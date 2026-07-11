# Mod 静态验证工具

本目录提供《神器使》Stellaris Mod 的统一静态验收入口。工具只读取仓库文件，不会改写脚本、贴图或存档。

## 使用方法

在仓库根目录运行：

```powershell
node tools/build/validation/validate-mod.js
```

也可以显式指定实际 Mod 目录：

```powershell
node tools/build/validation/validate-mod.js C:\path\to\SevenDays_Mod\mod
```

## 当前检查范围

- `descriptor.mod` 的版本与兼容版本字段。
- `.txt`、`.gfx`、`.asset`、`.gui`、`.mod` 的 UTF-8 BOM 与花括号结构。
- 简体中文本地化文件的 UTF-8 BOM、语言头和重复 key。
- Stellaris 4.4.3 已失效的 `trade_value` 资源键。
- 项目自有 `.gfx` 贴图引用。
- 命运之主固定设计所引用的项目部件与区段模板。
- 岗位、岗位修正、特质和巨构总览图标的已知缺口。

## 美术暂缓与严格模式

当前图标会等待统一美术规范后再补齐，因此默认运行时只把图标缺口显示为警告，不会让检查失败。

美术规范确定后，可以启用严格模式：

```powershell
node tools/build/validation/validate-mod.js --strict-art
```

严格模式会把岗位、岗位修正、特质和巨构总览图标缺口视为阻断项。

## 暂不覆盖的检查

- 游戏引擎才能确认的 trigger、effect 和 scope 合法性。
- 原版资源、原版贴图和原版部件是否存在。
- 事件 ID 的语义级重复检查。
- 游戏内界面布局、领袖招募、舰船航行和巨构建造流程。

这些项目继续通过新开局测试与 `error.log` 验收。

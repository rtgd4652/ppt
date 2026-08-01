# 构建与测试流程

## 1. 静态检查

执行：

```powershell
powershell -ExecutionPolicy Bypass -File tools/prototypes/aemusa_flagship/scripts/check_prototype.ps1
```

检查通过不等于游戏内行为通过，只说明目录、编码、引用和括号未发现已知静态错误。

## 2. 组装

执行：

```powershell
powershell -ExecutionPolicy Bypass -File tools/prototypes/aemusa_flagship/scripts/build_prototype.ps1
```

脚本只写入本原型的 `build/`，不会修改 `mod/` 或用户文档目录。

## 3. 最小回归顺序

1. 新开局，只启用原型 Mod。
2. 运行 `event aemusa_fp.1`。
3. 确认舰船设计器出现原型旗舰，必需核心齐全，可修改并保存设计。
4. 确认舰船可以超空间航行和跃迁。
5. 确认两个光环槽可分别安装友军与敌军原型光环。
6. 摧毁旗舰，确认首都星系只恢复一艘且处于独立编队。
7. 保存多个同舰种设计后重复摧毁测试，记录恢复了哪个设计。
8. 运行 `event aemusa_fp.10`，确认审计结果与实际一致。
9. 运行 `event aemusa_fp.20`，逐项测试缺失、重复与部署锁定故障。
10. 检查最新 `error.log`，只记录含 `aemusa_fp` 的错误。

## 4. 通过门槛

- 没有缺失必需组件导致的设计保存失败。
- FTL 与跃迁均能执行。
- 正常路径始终只有一个有效实例。
- 摧毁后不会在原位置和首都同时留下两个实例。
- 国家局势与账本状态一致，但局势自身不生成任何对象。
- 多设计恢复行为有明确结论；若不能精确恢复，则按已批准方案回退到固定预制设计。

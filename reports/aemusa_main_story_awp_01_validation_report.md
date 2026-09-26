---
title: "爱缪莎 1.0 主线 AWP-01 验证报告"
type: "implementation_validation_report"
version: "1.0"
status: "runtime_pass"
last_updated: "2026-08-16"
---

# 爱缪莎 1.0 主线 AWP-01 验证报告

## 1. 验证范围

本报告只验证主线最小运行骨架：路线初始化、事件簇生命周期、白夜馆只读入口与无剧情测试探针。不验证序章及后续正式剧情、奖励、危机、舰船、巨构、终局权限或结局。

## 2. 静态检查结果

| 检查项 | 结果 | 证据 |
| --- | --- | --- |
| 路线版本 | 通过 | `ASR-002` 固定为版本 `1`，状态为 `formal_awp_01` |
| 扩展登记表 | 通过 | 650 项，0 个重复 key，剩余 6 个待审枚举 |
| 状态引用 | 通过 | AWP-00/01 脚本直接访问的 52 个主线状态 key 全部已登记 |
| 生命周期接口 | 通过 | 开始、完成、唯一结算分别检查前置状态，不允许重复写入 |
| 白夜馆入口 | 通过 | 入口只调用只读路由器和无剧情状态页，不推进路线 |
| namespace 与事件 ID | 通过 | `aemusa_ms` namespace 唯一；定义 `.1/.2/.3/.90/.91/.92` |
| scripted 定义 | 通过 | 新增 trigger/effect 在 Mod 内无重复定义 |
| 非本地化脚本编码 | 通过 | 3 个 AWP-01 新增 `.txt` 均为 UTF-8 无 BOM |
| 本地化编码 | 通过 | 中文 `.yml` 保留 UTF-8 BOM |
| 花括号与空白 | 通过 | 3 个新增脚本花括号匹配，无尾随空白，`git diff --check` 无补丁错误 |

## 3. 游戏内运行时复测

以下测试必须在只启用本 Mod 的 Stellaris 4.4.3 测试环境完成。

### 3.1 新开局与只读入口

1. 使用神器使主物种建立玩家国家并新开局；
2. 打开白夜馆，确认出现“爱缪莎主线”；
3. 打开该入口，确认显示“序章之前”的骨架状态页；
4. 关闭并重复打开，确认没有开始事件簇、推进章节或执行结算；
5. 保存并读档，再次打开，确认入口与页面状态一致。

旧测试存档如果没有执行新开局初始化，可在玩家国家作用域执行：

```text
event aemusa_ms.1
```

### 3.2 生命周期与唯一结算探针

警告：以下步骤会写入 `AED-PRO-10` 的测试状态，只能在可丢弃测试存档使用。

1. 在玩家国家作用域执行：

   ```text
   event aemusa_ms.90
   ```

2. 让游戏经过至少 3 天；
3. 检查 `game.log`，预期出现：
   - `AEMUSA-MS|PASS|awp_01_route_version`
   - `AEMUSA-MS|PASS|awp_01_probe_consistency`
   - `AEMUSA-MS|PASS|awp_01_probe_settled`
   - 0 项 AWP-01 `FAIL`
4. 再次执行 `event aemusa_ms.90` 并经过 3 天，确认不会重复开始或结算；
5. 保存并读档后执行：

   ```text
   effect aemusa_ms_log_awp_01_probe = yes
   ```

6. 确认仍为 3 项 `PASS`、0 项 `FAIL`。

### 3.3 聚合审计与错误日志

在路线已经初始化的玩家国家作用域执行：

```text
effect aemusa_ms_log_state_audit = yes
```

预期 AWP-00 聚合审计更新为 12 项 `PASS`、0 项 `FAIL`，并具有完整的开始／结束记录。随后检查最新 `error.log`：凡包含 `aemusa_ms_story_entry_triggers.txt`、`aemusa_ms_story_lifecycle_effects.txt`、`aemusa_main_story_events.txt` 或相关 key 的解析、作用域、未知触发器与未知效果错误均视为不通过。

## 4. 第一次运行时检查记录

2026-08-16 16:06 至 16:07 的最新日志确认：

- AWP-01 生命周期探针连续执行三次；
- 每次均获得 `awp_01_route_version`、`awp_01_probe_consistency`、`awp_01_probe_settled` 三项 `PASS`；
- AWP-01 `FAIL` 为 0；
- 聚合审计获得 12 项 `PASS`、0 项 `FAIL`；
- 审计开始与 `writes=none` 结束标记完整；
- `error.log` 中没有 `aemusa_ms`、AWP-01 新增文件或相关接口的解析、作用域、未知触发器和未知效果错误。

这证明路线版本、生命周期、重复探针幂等性、唯一结算和聚合一致性已通过核心运行时验证。

## 5. 人工界面与存读档验收

2026-08-16，人工复测确认：

- 白夜馆正常显示“爱缪莎主线”入口；
- 入口正常打开“序章之前”的只读状态页；
- 页面明确说明不会开始事件簇、推进章节或执行结算；
- 保存并重新读档后，入口和只读状态仍然正常；
- 没有观察到重复初始化、重复结算或入口丢失。

## 6. 当前结论

AWP-01 已通过静态、核心运行时、人工界面和保存／读档门禁，状态正式更新为 `runtime_pass`。AWP-01 实施完成；AWP-02 尚未获得实现授权，不得自动开始。

> 后续状态索引（2026-09-26）：以上保留本报告验收时的结论。AWP-02 随后已获单独授权并实现，当前仍待运行验收，见 [工作包执行记录](../docs/design/aemusa_main_story_implementation_work_packages_v1.0.md) 与 [AWP-02 报告](aemusa_main_story_awp_02_validation_report.md)。本注不改变 AWP-01 的历史测试证据。

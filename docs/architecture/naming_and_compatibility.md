# 命名与兼容规范

## 1. 公共标识稳定性

以下内容一旦进入可发布版本，即视为公共接口：

- 游戏对象 key。
- 事件 namespace 与事件 ID。
- scripted effect 和 scripted trigger 名称。
- country、planet、leader、ship flag。
- event target 名称。
- 本地化 key。
- GFX sprite 名称。

公共接口不得只为“看起来整齐”而批量重命名。重命名会破坏存档、事件引用、设计引用或其他模块依赖。

## 2. 新内容前缀

v0.2 以后新建内容统一使用 `aemod_` 前缀：

```text
aemod_white_night_*
aemod_leader_aemusa_*
aemod_leader_antoniva_*
aemod_leader_yanhua_*
aemod_economy_*
aemod_progression_*
aemod_destiny_city_*
aemod_fate_observatory_*
aemod_destiny_lord_*
aemod_debug_*
```

现有 `aemusa_*`、`artifact_*` 和 `destiny_lord` key 继续保留。新前缀不意味着立即重命名旧对象。

## 3. 文件命名

```text
aemod_<模块>_<对象类型>.txt
aemod_<模块>_l_simp_chinese.yml
```

示例：

- `aemod_white_night_events.txt`
- `aemod_leader_antoniva_effects.txt`
- `aemod_destiny_lord_components.txt`
- `aemod_progression_l_simp_chinese.yml`

文件名描述所有权，对象 key 描述运行接口。移动对象到新文件时可以保留旧 key。

## 4. 事件规范

- 一个功能模块使用一个明确 namespace。
- 角色使用独立 namespace，不把新角色事件继续加入 `aemusa_dialogue`。
- 每个事件文件顶部说明事件范围和作用域。
- 隐藏事件也必须写中文注释说明触发来源。
- 白夜馆事件只负责路由，角色业务逻辑进入角色 namespace。

建议事件段：

| 范围 | 用途 |
| --- | --- |
| `.1-.49` | 主入口与状态页 |
| `.50-.99` | 招募确认 |
| `.100-.199` | 通讯与职业选择 |
| `.200-.299` | 成长与等级节点 |
| `.300-.399` | 角色历史与扩展内容 |
| `.900-.999` | 迁移、兼容和调试 |

## 5. flag 与 event target

- 永久进度使用 country/planet/leader flag。
- event target 只用于需要直接引用对象的流程，不应代替永久状态 flag。
- flag 命名必须包含模块和语义，例如 `aemod_destiny_city_created`。
- 已经进入存档的旧 flag 不重命名；需要新名称时，在兼容事件中同步一次。
- 唯一领袖同时保留领袖 flag 与国家级招募 flag，分别处理对象识别和防重复。

## 6. 本地化与 GFX

- 本地化 key 使用英文、数字和下划线。
- 简体中文 `.yml` 使用 UTF-8 BOM。
- `.txt`、`.gfx`、`.asset`、`.gui` 使用 UTF-8 无 BOM。
- GFX 名称统一使用 `GFX_aemod_<模块>_<用途>`。
- 正式图标文件名与对象 key 对齐；在美术规范确定前只登记缺失资源，不批量生成临时正式图标。

## 7. 中文注释

所有新增 Stellaris 脚本必须包含中文注释，至少解释：

- 对象用途。
- 关键作用域。
- 防重复或兼容逻辑。
- 非显而易见的引擎限制。
- 暂时降级内容及恢复条件。

注释不重复翻译每个字段，也不把尚未实现的设想写成现有功能。

## 8. 兼容迁移

需要调整旧对象时按以下顺序处理：

1. 保留旧 key。
2. 将定义移动到目标模块文件。
3. 更新内部调用，但不改变存档可见标识。
4. 运行静态验证。
5. 使用旧存档和新开局分别测试。
6. 稳定一个版本后，才考虑增加弃用说明。

严禁在一次提交中同时完成批量重命名、逻辑改写和数值平衡。

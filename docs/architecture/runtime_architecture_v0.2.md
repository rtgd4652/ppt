# v0.2 运行架构

## 1. 基本原则

Stellaris 运行文件必须继续放在引擎规定的目录中。为避免不同版本对递归子目录加载行为产生差异，`common/<类型>/` 和 `events/` 内采用扁平文件布局，通过统一文件名前缀表达模块归属。

新文件统一使用：

```text
aemod_<模块>_<对象类型>.txt
```

现有 v0.1 文件暂不强制改名；它们作为兼容层保留，迁移时只移动定义，不修改公共 key。

## 2. 模块划分

| 模块 | 职责 | 当前主要文件 | v0.2 目标 |
| --- | --- | --- | --- |
| core | 物种、肖像集合、起源、预设帝国、公共触发条件 | `aemusa_origins.txt`、物种目录、预设帝国 | 提供其他模块依赖的文明身份，不依赖角色模块 |
| white_night | 招募、联络、名册和档案入口 | `aemusa_dialogue_events.txt`、白夜馆法令 | 只负责界面路由，不直接编写角色创建细节 |
| leader_aemusa | 爱缪莎创建、职业切换、等级立绘 | `aemusa_leader_effects.txt`、部分对白事件 | 独立效果与事件文件，保留旧 key |
| leader_seth | 赛斯创建、状态与后续通讯 | `aemusa_leader_effects.txt`、部分对白事件 | 独立效果与事件文件 |
| leader_yutong | 幽桐创建、状态与后续通讯 | `aemusa_leader_effects.txt`、部分对白事件 | 独立效果与事件文件 |
| leader_rabi | 拉比创建、状态与后续通讯 | `aemusa_leader_effects.txt`、部分对白事件 | 独立效果与事件文件 |
| leader_antoniva | 安托涅瓦资料与未来实装 | 当前只有知识库和设计文档 | v0.2 新模块，不写入爱缪莎文件 |
| leader_yanhua | 晏华资料与未来实装 | 当前只有知识库和设计文档 | v0.2 新模块，不写入爱缪莎文件 |
| economy | 建筑、区划、岗位、资源转换 | `aemusa_buildings.txt`、`aemusa_districts.txt`、岗位文件 | 与角色事件解耦，只依赖 core/progression |
| progression | 科技、传统、飞升和解锁关系 | 科技、传统、飞升文件 | 统一掌握解锁，不直接创建领袖 |
| destiny_city | 专属星球和防重复逻辑 | 命运都市决议、行星类别 | 以永久 flag 和行星标记作为唯一状态源 |
| fate_observatory | 巨构阶段与政策模式 | 命运观测塔、政策文件 | 独立巨构模块，模型资源后置 |
| destiny_lord | 舰体、区段、组件、设计、重构事件 | 命运之主相关文件 | 与普通军备组件分离，模型 locator 完成后再恢复武器槽 |
| debug | 测试法令、测试效果与诊断输出 | debug 法令、效果、修正 | 与正式内容隔离，发布前可统一隐藏 |

## 3. 依赖方向

允许的依赖方向：

```text
core
├── economy
├── progression
├── destiny_city
├── white_night ──→ leader_*
├── fate_observatory ──→ progression
└── destiny_lord ──→ progression + fate_observatory
```

约束：

- `core` 不得反向依赖白夜馆或具体角色。
- 白夜馆只调用角色模块公开的 scripted effect 或事件入口。
- 角色模块不得直接修改白夜馆主菜单结构。
- 经济模块不得直接创建领袖。
- 科技、传统和飞升的解锁关系统一放在 progression 模块。
- 命运之主与命运观测塔不得成为普通角色招募的前置依赖。

## 4. 目标文件布局

以下是目标命名，不代表需要一次性迁移：

```text
mod/events/
  aemod_white_night_events.txt
  aemod_leader_aemusa_events.txt
  aemod_leader_antoniva_events.txt
  aemod_leader_yanhua_events.txt
  aemod_destiny_lord_events.txt

mod/common/scripted_effects/
  aemod_leader_aemusa_effects.txt
  aemod_leader_seth_effects.txt
  aemod_leader_yutong_effects.txt
  aemod_leader_rabi_effects.txt
  aemod_leader_antoniva_effects.txt
  aemod_leader_yanhua_effects.txt
  aemod_debug_effects.txt

mod/common/on_actions/
  aemod_on_actions.txt

mod/localisation/simp_chinese/
  aemod_core_l_simp_chinese.yml
  aemod_white_night_l_simp_chinese.yml
  aemod_leaders_l_simp_chinese.yml
  aemod_economy_l_simp_chinese.yml
  aemod_progression_l_simp_chinese.yml
  aemod_destiny_content_l_simp_chinese.yml
```

## 5. 集成接口

### 白夜馆调用角色

白夜馆只判断角色模块公开状态，并调用公开入口：

```text
可见条件 → 招募状态 → 角色公开事件或 scripted effect → 返回白夜馆
```

公开状态应使用稳定的国家 flag、领袖 flag 或 event target。白夜馆不得复制角色创建代码。

### on_action

所有 on_action 注册保留在一个集成文件中，再转发到模块事件。避免多个窗口同时修改同一个原版 on_action 块，也避免覆盖顺序不清。

### 本地化

本地化按模块拆分，但每个 key 全仓库只能定义一次。拆分时执行“从旧文件删除，再加入新文件”，禁止复制后保留重复 key。

### 美术

运行期 DDS、MESH、GFX 和 ASSET 继续放在 `mod/gfx/`。源图、Blender 文件、贴图工程和预览图只放在 `assets/`。正式风格未确定前不补缺失图标。

## 6. 所有权规则

- 角色线只修改自己的事件、效果、trait 与本地化文件。
- 白夜馆线拥有白夜馆主菜单和路由文件。
- 经济线拥有建筑、区划和岗位。
- 舰船线拥有命运之主舰体、区段、组件、设计和模型。
- 巨构线拥有命运观测塔脚本、政策和模型。
- 总控线拥有 descriptor、on_action 集成、版本文档和最终合并。

跨模块修改必须由总控线执行或在提交说明中明确列出。

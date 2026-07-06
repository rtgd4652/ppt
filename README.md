# SevenDays_Mod

《永远的七日之都》主题 Stellaris Mod 项目仓库。

## 仓库结构

```text
SevenDays_Mod/
├── mod/             # 真正给 Stellaris 加载的模组目录
├── knowledge/       # 七日之都世界观、角色、组织、时间线知识库
├── assets/          # 开发期素材，不直接作为最终 Mod 根目录加载
├── docs/            # 路线图、设计文档、TODO、变更记录
├── tools/           # 爬虫、解析、导出、构建辅助工具
└── README.md
```

## 本地加载方式

Stellaris 启动器应该指向 `mod/` 目录，而不是仓库根目录。

当前实际模组目录：

```text
C:\Users\Admin\Desktop\ppt\simple_leader_edict\mod
```

`mod/descriptor.mod` 是真正给游戏读取的描述文件。仓库根目录只负责管理源码、素材、文档和工具。

## 开发约定

- `mod/` 内只放游戏运行需要读取的内容。
- `assets/official_reference/` 只放参考资料，不作为最终 Mod 内容发布。
- AI 图、Blender 源文件、概念图放入 `assets/ai_generated/` 或对应素材目录。
- 生成脚本、转换脚本、导出脚本放入 `tools/`。
- 所有 Stellaris 脚本继续添加中文注释。
- 不覆盖原版文件，尽量保持纯新增。

## 当前核心内容

- 神器使物种、特质、起源、预设帝国。
- 白夜馆通讯入口与领袖召唤框架。
- 爱缪莎领袖、职业切换、等级成长与立绘切换。
- 专属传统、飞升、科技、建筑、区划、岗位。
- 命运之主舰船、专属组件、武器、光环与模型。
- 命运观测塔巨构与后续建模规划。


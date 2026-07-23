# 七日之都 Wiki 采集工具

## 分层职责

- `BrowserManager`：只负责浏览器、Cloudflare 会话、页面内请求与截图。
- `WikiClient`：只封装 MediaWiki API。
- `Parser`：只负责 HTML 到 Markdown，不联网、不访问浏览器、不访问 API。
- `CharacterCollector`：只串联 `WikiClient → Parser → Markdown` 流程，不写解析逻辑。
- `StoryCollector`：只串联 `WikiClient → StoryParser → Markdown` 流程；剧情页默认先保存完整文本，再进入人工摘要层。

## BrowserManager 接口

```js
const { BrowserManager } = require("./src/browser-manager");

const browser = new BrowserManager();

await browser.start();          // 启动浏览器并复用用户数据目录
await browser.goto(url);        // 打开页面
await browser.wait_ready();     // 等待页面完全加载，包括 Cloudflare Challenge
const html = await browser.html();        // 获取最终 HTML
const image = await browser.screenshot(); // 调试截图，返回截图路径
const file = await browser.download(url); // 在当前会话下下载资源
await browser.close();          // 关闭浏览器
```

## 连通性检查

```powershell
cd C:\Users\Admin\Desktop\ppt\simple_leader_edict\tools\crawler
npm run check:f7d
```

如果浏览器出现 Cloudflare 验证，请手动完成。验证通过后，浏览器数据会保存到 `.playwright-profile/`，下次运行会复用。

## Milestone 1：单角色知识卡

默认生成安托涅瓦：

```powershell
npm run collect:character
```

生成指定角色：

```powershell
npm run collect:character -- 爱缪莎
```

输出位置：

```text
raw/huiji/characters/<角色名>.raw.md
knowledge/characters/<角色名>.md
indexes/images/<角色名>.images.json
```

注意：

- `raw/huiji/characters/` 保存完整原始 Markdown，便于回溯。
- `knowledge/characters/` 保存清洗后的知识库 Markdown。
- `indexes/images/` 保存图片名称、URL、文件页和粗分类。
- Milestone 1.1 不下载图片，只记录图片索引。

## MOD 摘要资料

生成既有七名角色的批量摘要：

```powershell
npm run modready:characters
```

为单个已采集角色生成独立摘要与报告，例如主线剧情 2 的角色“安”：

```powershell
npm run modready:character -- 安
```

单角色命令只写入对应的 `knowledge/mod_ready/characters/<角色名>.mod.md`，并生成独立报告，避免覆盖既有七名角色的批量验收报告。

## Wiki 剧情文本迁移

剧情知识库现以灰机 Wiki 的公开文本为正文主来源。视频抽样记录保留为补充线索，但不再用于决定剧情正文。

先收集单一剧情页（默认是已确认存在的“正轨的箱庭/剧情/第七天”）：

```powershell
npm run collect:story
```

对已经人工确认的有限页面清单，可以在同一浏览器会话中批量采集：

```powershell
node scripts/collect-story-page.js --batch "深渊的步伐/剧情/第七天" "深渊的步伐/剧情/第六天"
```

批量模式不会自动发现或同步全站，只处理命令行明确列出的页面。分支日、最终日和特殊失败页仍需先从路线总页人工确认，再逐项加入清单。

生成：

```text
raw/huiji/stories/<页面名>.raw.md
knowledge/story/pages/<页面名>.md
indexes/story_pages/<页面名>.source.json
```

如需从已采集页面发现候选剧情链接，而不直接抓取全站：

```powershell
npm run discover:story
```

候选链接会写入 `indexes/story_pages/discovery/`，必须经过页面范围分类后才能进入正式批量清单 `tools/knowledge/data/huiji_story_text_manifest_v0.1.json`。

## 剧情选择树保留规则

灰机 Wiki 的剧情页通常用 `nav-tabs / tab-content` 保留“选项标签 → 对应对白”的原始关联。`StoryParser` 优先直接读取该 HTML 结构，而不是从线性 Markdown 猜测归属；每个选项卡都会在 clean 文件中保留为独立的“选项 / 条件 / 版本 → 来源文本”块。

分支会严格分为三类：

- `player_or_dialogue_choice`：玩家或对话选择；默认按一次性分支记录。
- `state_condition`：由周目、黑核、区域解放等已记录游戏状态决定的分支，不写成玩家选择。
- `source_version`：Wiki 的“改版前 / 改版后”资料对照，不写成游戏内选择。

只有同时满足下列证据时，才标记 `repeatable: true`：

- 前后两组 Tab 的旧选项完全一致；
- 对应回答逐项完全一致；
- 第二组仅额外提供一个明确退出选项；
- 两组之间的页面文本明确说明这是同一组选项的再次询问。

不满足以上条件的分支绝不推断为可重复。HTML 不保留结构的旧式页面，才回退到同样严格的线性文本核对逻辑。所有结构元数据写入 `indexes/story_pages/*.source.json` 与本地 SQLite 的 `story_choice_trees`；`raw/` 层永远不加入这些结构化标记。

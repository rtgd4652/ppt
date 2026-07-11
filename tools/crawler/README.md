# 七日之都 Wiki 采集工具

## 分层职责

- `BrowserManager`：只负责浏览器、Cloudflare 会话、页面内请求与截图。
- `WikiClient`：只封装 MediaWiki API。
- `Parser`：只负责 HTML 到 Markdown，不联网、不访问浏览器、不访问 API。
- `CharacterCollector`：只串联 `WikiClient → Parser → Markdown` 流程，不写解析逻辑。

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

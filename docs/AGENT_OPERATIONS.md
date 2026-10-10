# 智能体接手：可用操作与执行条件

更新：2026-10-10。用于更换模型、智能体或会话后恢复已经掌握的操作能力。当前开发任务仍以[项目进度](PROJECT_STATUS.md)、[执行清单](TODO.md)和最新续接记录为准。

**这是一份能力记录，不是待执行命令队列。** 历史宣战、投降、资源补充和剧情测试命令不应自动重放；旧收工记录也不能代替用户本轮指令。先确认当前目标、实际窗口和存档，再执行必要操作。

**当前范围调整（2026-10-10）：人物组合暂时跳过，后面由用户决定。** 新增自由协作与固定搭档均暂缓；此前“工程试制”的人物搭配只是未实施建议，不自动恢复。已完成首都工坊及十人分级核心保留；随后[C1文明路线梳理与说明修正](../reports/artifact_civilization_route_c1_2026-10-10.md)已完成，静态通过，没有操作游戏或创建存档。下一包建议为殖民地应急预案，尚未实现。用户补充现有15座建筑图标后续全部用绘图工具重绘，按[资产清单](art/ASSET_PRODUCTION_PLAN.md)续接。

## 接手时先做什么

1. 读取仓库 `AGENTS.md`、当前进度和最新工作包记录；检查北京时间。通常22:30开始收尾、23:00前完成保存。单次延长只在用户指定的当晚有效。
2. 枚举当前工具和插件；需要 Computer Use 时先查插件及 `codex plugin list`，不把“这一会话没有该工具”说成“从来无法操作游戏”。插件名称、安装状态、实际可调用入口分别核实；普通插件检索不包含全部本地市场。
3. 检查Git改动、游戏是否已运行、启用的Mod、当前真实画面。保留用户文件和原存档，不恢复旧测试任务。
4. 优先复用已通过的操作和测试证据。只验证当前新增流程、必要读档和改动涉及的严重失败点，不每窗另存、不例行计算哈希、不重复全套审计。
5. 仅操作群星所在窗口／屏幕。另一屏幕留给用户看视频。失焦立即停止新按键或点击；不要通过全桌面坐标猜测目标。

## 已有能力与当前状态

| 操作 | 状态与条件 | 入口／证据 |
| --- | --- | --- |
| 读写项目、中文Git提交、运行定向检查 | 已使用；遵守当前用户范围和文件规范 | `tools/validation/README.md`、`AGENTS.md` |
| 启动群星 | 已验证；2026-10-10由智能体直接启动到4.5.2主菜单 | 下方启动命令；[B2当日记录](../reports/artifact_growth_batch_b2a_runtime_2026-10-10.md) |
| Computer Use插件安装与窗口API | 2026-10-10按用户要求安装成功；同一会话导入sky，实际完成识别、置前、截图、菜单载档和另存新档 | `codex plugin add computer-use@openai-bundled --json`；版本26.818.41509 |
| 正常关闭、冷启动 | 已验证；关闭前先保存必要成果，只向已识别进程发送正常关闭请求 | [B1记录](../reports/artifact_growth_batch_b1_2026-10-09.md)、[B2首批记录](../reports/artifact_growth_batch_b2a_2026-10-09.md) |
| 识别群星PID、窗口、前台、布局、Caps Lock | 已验证；今天仓库内脚本也成功 | `tools/desktop/Send-StellarisText.ps1 -Action Inspect` |
| 置前与仅游戏窗口截图 | 已验证，但Windows可能拒绝置前；拒绝时没有发送输入 | 同脚本 `Activate`／`Capture`；2026-10-09及10-10复测 |
| 完整英文控制台输入、自动回车、开关控制台 | 2026-10-07实际验证；今天已验证脚本可运行及字符映射，未重新验证全部输入 | [键盘修复记录](../reports/stellaris_keyboard_input_repair_2026-10-07.md)；仓库内脚本为当时版本的完整复制 |
| 只对当前群星窗口的鼠标点击 | 新增守卫脚本，语法通过；本轮单次载入菜单点击后实际进入菜单，截图刷新有延迟；当前优先使用Computer Use | `tools/desktop/Invoke-StellarisClick.ps1`；不能仅凭返回码声称菜单已改变 |
| 载档、法令、通讯选项和暂停／运行 | 2026-10-10使用Computer Use正常完成；历史批次也操作过舰队、星港和巨构 | [B2当日记录](../reports/artifact_growth_batch_b2a_runtime_2026-10-10.md)；旧入口按需复用，不重新全部验证 |
| 另存与自定义英文档名 | 另存已验证；`type_text`、Ctrl+A及Escape本轮没有被游戏可靠接收，自定义档名仍未修好 | 本轮先确认默认日期名未占用，再正常保存`2246.07.26`／`2247.01.25`，前一新档也成功载回；名称必须指定时才让用户完成输入 |
| 只读游戏日志、压缩存档 | 已使用，可核对实际结果；读档文件不改写 | [A批存档读回](../reports/artifact_engineering_batch_a_save_readback_2026-10-09.json)；复用结构化解析器定位玩家国家，不全文件正则猜状态 |
| Python原画裁切／DDS构建 | 既有用户授权和已验证生产脚本；按当前资产范围使用 | `tools/build/prepare_companion_portraits.py`、里程碑4肖像记录 |
| Blender离线建模、材质、PDX导出、预览 | 5.1.2离线流程成功；不会自动替代用户打开的Blender场景 | [模型源与构建说明](../art/models/milestone4_surface_v02/README.md)、[材质样品记录](../reports/milestone4_surface_assets_2026-10-08.md) |
| Blender MCP | 当前有对应工具，不等于已连接或场景已授权修改；先只读场景确认 | `get_scene_info` 等实际暴露入口；离线流程可独立使用 |
| Git上传 | 2026-10-09原积累251提交及保存说明已上传；同一已批准范围不重复索要确认 | [收工与上传记录](../reports/development_closeout_2026-10-09.md)；其他仓库、发布或范围不能由此自动授权 |

## 当前机器路径与环境

```text
仓库：C:\Users\Admin\Desktop\ppt\simple_leader_edict
游戏：F:\steam\steamapps\common\Stellaris\stellaris.exe
用户目录：C:\Users\Admin\Documents\Paradox Interactive\Stellaris
本地Mod：上述仓库\mod
保留起点：save games\_-258619271\A-capital-workshop-done-2246.sav
本轮进行档：同目录\2246.07.26.sav（已正常载回一次）
本轮结果档：同目录\2247.01.25.sav（当前游戏暂停；能源为0）
```

目标版本4.5.1；近期实际启动为4.5.2，两者不等于已经完成兼容验收。测试仅启用 `mod/aemusa_artifact_user.mod`。`dlc_load.json`及注册路径应读回确认，不为测试覆盖用户原播放集或配置。

2026-10-10会话开始时Computer Use未安装，旧缓存路径不存在，普通插件检索也未返回匹配项；随后 `codex plugin list`在已配置的官方本地市场中明确列出该插件。用户要求“没有就安装”，CLI安装成功并恢复同版本路径，随后sky在本会话可用。**接手应先查CLI本地市场，不能仅凭缓存缺失或普通插件搜索下结论。**

## Computer Use：优先的窗口操作入口

```powershell
# 列表可核对本地市场，不需要修改配置。
codex plugin list
codex plugin add --help
# 仅在用户要求安装或该安装已获授权时使用；不手改config.toml冒充安装。
codex plugin add computer-use@openai-bundled --json
```

安装结果返回实际 `installedPath`，到该目录读取 `skills/computer-use/SKILL.md`，以及它要求的 `docs/guidance.md`、`docs/confirmations.md`；需要API签名时读 `docs/api.md`。[官方插件文档](https://developers.openai.com/plugins/build/plugins)说明本地市场与缓存结构；本机CLI的 `add --help` 给出实际安装参数。普通全局插件检索不代替本机市场检查。

本机验证路径：

```text
C:\Users\Admin\.codex\plugins\cache\openai-bundled\computer-use\26.818.41509
```

初始化使用 `node_repl`，直接导入官方包，不启动helper exe，不自行实现helper协议：

```javascript
if (!globalThis.sky) {
  globalThis.sky = (await import('@oai/sky')).sky;
}
globalThis.gameWindows = (await sky.list_windows()).filter(
  w => /stellaris/i.test(w.app + ' ' + (w.title || ''))
);
nodeRepl.write(JSON.stringify(gameWindows));
```

先检查返回对象确为唯一群星，再在下一单元获取该返回窗口：

```javascript
if (gameWindows.length !== 1) throw new Error('Expected one returned game window');
globalThis.gameWindow = await sky.get_window({
  id: gameWindows[0].id, app: gameWindows[0].app
});
await sky.activate_window({window: gameWindow});
globalThis.gameState = await sky.get_window_state({window: gameWindow});
globalThis.gameWindow = gameState.window;
```

看返回的真实截图后，在下一单元只执行一次动作并立即刷新。坐标、截图ID、元素索引仅来自上一观察，不复用旧PID或猜窗口对象。游戏UI通常没有有效可访问性文本，默认截图即可；需要输入时先观察实际输入焦点。截图由工具直接显示，不再解码或重复保存仅为查看。

2026-10-10实际正常入口为：政府→政策与法令→联络白夜馆→神器使通讯／名册→安或丽→人物任务。关闭通讯与政策页后，右下角游戏菜单可以正常载入／保存。这里只记录页面名称；坐标随布局变化，不保存一串坐标让下一智能体盲点。

如果返回窗口元数据写着群星，截图却是聊天或其他应用，也必须停止输入。重新列出唯一群星、置前并刷新，看到真实游戏后才继续；元数据不代替画面确认。遇到`user input was detected`，重新观察并适应用户的操作，不直接重复旧点击；若明确报告用户停止Computer Use或回合已结束，停止界面输入。

`click`、`press_key`、`type_text`、`scroll`等都指定该返回Window；目标只选群星，不操作另一屏幕。原版游戏控制台不是Windows终端，可以在当前测试授权内输入游戏命令，但仍必须确认输入完整及真实回显。

插件加载后Windows界面自动化只用它的JS API；同轮不再混用PowerShell UI自动化，也不通过插件操作Windows终端、运行框、认证、安全设置或Codex自身界面。下面原生脚本仅作为没有该插件的其他会话的已知后备入口。普通读写仓库、日志和Git不属于Windows界面自动化。

桌面脚本在普通沙盒执行上下文可能看不到真实窗口，应使用执行器的桌面权限上下文并检查实际结果。当前通过 `exec_command` 的 `require_escalated` 成功启动／识别／截图；这是执行器访问桌面的权限，不要求把游戏改为Windows管理员运行，不关闭安全设置。若自动审批拒绝，记录原因并在授权范围内处理，不换接口绕过拒绝。

## 启动、识别与截图

以下命令在仓库根目录、实际桌面执行器上下文运行。启动前先查进程；已有群星时不要再启动一份。

```powershell
Get-Process -Name stellaris -ErrorAction SilentlyContinue |
    Select-Object Id, Path, MainWindowHandle, StartTime

# 仅在没有已运行游戏时启动交互窗口。
Start-Process -FilePath 'F:\steam\steamapps\common\Stellaris\stellaris.exe' `
    -WorkingDirectory 'F:\steam\steamapps\common\Stellaris' -WindowStyle Normal

& '.\tools\desktop\Send-StellarisText.ps1' -Action Inspect
& '.\tools\desktop\Send-StellarisText.ps1' -Action Activate -Label game_current
```

`Activate`成功时也生成截图；群星已在前台时可直接 `Capture`。用 `view_image` 查看返回的本地PNG，再决定下一步；只看到脚本成功不是游戏接受操作的证据。

正常退出：确认需要保存的进度已经保存，重新识别唯一游戏进程，再调用该进程的 `CloseMainWindow()`；检查是否出现保存提示或进程已退出。不要强制终止未保存游戏。

## 扫描码输入的正确用法

仓库内稳定入口：[Send-StellarisText.ps1](../tools/desktop/Send-StellarisText.ps1)。外部排障目录 `C:\Users\Admin\Desktop\ppt\stellaris-keyboard-input-fix` 保留原脚本、HANDOFF、DIAGNOSTICS和截图；克隆仓库后不依赖该外部目录才能找到输入脚本。

默认每键100ms、间隔80ms；命令必须是单行可打印ASCII，最多1400字符。它只发送扫描码，不粘贴中文、不后台输入。中文键盘布局 `08040804` 可以处于英文模式，不能仅凭布局编号判断输入法模式。

1. 看图确认控制台已经打开、输入行空白、游戏前台、无其他菜单接收输入。
2. 写单行UTF-8命令到本机临时文本；先 `ValidateText`，再 `Text`。**Text不会回车。**
3. 看输出截图，逐字核对实际命令；只有一致时才用同一文件执行 `Submit`。
4. 核对真实回显／游戏日志／实际界面，再关闭控制台。不要在失焦后重复提交同一条可能已执行的命令。

下面只用无状态修改的 `help` 示例；不是每次接手都必须重跑：

```powershell
$probeFile = Join-Path $env:TEMP 'stellaris_help_probe.txt'
[IO.File]::WriteAllText($probeFile, 'help', [Text.UTF8Encoding]::new($false))
& '.\tools\desktop\Send-StellarisText.ps1' -Action ToggleConsole -Label console_open
& '.\tools\desktop\Send-StellarisText.ps1' -Action ValidateText -TextFile $probeFile
& '.\tools\desktop\Send-StellarisText.ps1' -Action Text -TextFile $probeFile -Label help_typed
# 先查看help_typed.png，确认输入确实为help，再执行下一行。
& '.\tools\desktop\Send-StellarisText.ps1' -Action Submit -TextFile $probeFile -Label help_submitted
& '.\tools\desktop\Send-StellarisText.ps1' -Action ToggleConsole -Label console_closed
```

`Submit`要求与同PID、同窗口的上一条完整未提交输入记录一致；`pending-input.json`只是尝试记录，不是游戏收到文字的证明。控制台开关键也不识别当前是否已经打开，必须先看图。

若出现拼音候选：仅在确认当前内容来自刚才脚本、未提交且可以清除时用 `ClearText`；确认空行后 `ShiftMode`切换一次，再观察英文输入。不要盲目来回按Shift。部分输入、用户原输入和已提交文字不允许用这条清除动作猜测处理。

## 窗口内点击

新入口：[Invoke-StellarisClick.ps1](../tools/desktop/Invoke-StellarisClick.ps1)。它要求当前唯一游戏PID、游戏前台、120秒内参考截图、同尺寸窗口，以及归一化坐标落在游戏客户区；拒绝标题栏、边框和另一屏幕。失焦停止，只释放脚本自己按下的按钮。

```powershell
& '.\tools\desktop\Send-StellarisText.ps1' -Action Capture -Label before_click
# 看before_click.png确定目标，再填本次Inspect返回的PID及截图上的坐标比例。
& '.\tools\desktop\Invoke-StellarisClick.ps1' `
    -X 0.5 -Y 0.5 -ReferenceImage '.\tools\desktop\before_click.png' `
    -ExpectedGameProcessId $currentGamePid
& '.\tools\desktop\Send-StellarisText.ps1' -Action Capture -Label after_click
```

上例中心点仅说明参数，不能照抄点击；`$currentGamePid`须由本次识别结果填写。X/Y以**整张游戏窗口截图**宽高计算比例，含窗口标题区，脚本再检查点是否在客户区。每次界面变化后重新截图、查看结果，不能沿用旧截图批量点击。

## 失败时如何继续

| 失败／不确定 | 处理 |
| --- | --- |
| 工具列表没有Computer Use | 先检查 `codex plugin list`和实际安装状态；用户要求安装时按官方CLI安装并导入sky。全部核实后仍缺失才使用其他会话的后备入口，不让用户重复旧测试 |
| 窗口置前被Windows拒绝 | 不发送键或点击；请用户先回复准备好、随后点击群星；`Capture -WaitForFocusMs 30000`可等待。不要模拟全局快捷键来强抢前台 |
| 同时存在多个游戏／窗口 | 只读识别，不猜PID、不关闭未知窗口 |
| 窗口尺寸、PID或画面已变 | 重新Inspect和截图；不使用旧坐标、旧pending输入或旧截图 |
| Input attempted但画面没变化 | 说明尝试未证明被接收；按实际输入框／日志定位，不立即重复有副作用的命令 |
| 保存名无法自动输入 | 优先确认默认日期名称确实未被使用，再通过正常按钮另存，并读回新文件；不能覆盖同名旧档。必须用指定名称时才请用户输入，不重复尝试文字或逐窗另存 |
| 资源／快速完成测试 | 仅在当前隔离档和当前测试授权内使用，记明受控来源；可能切换AI作弊的命令须确认最终关闭。`instant_build`历史未形成充分实测，不能当作已验证入口 |
| 日志报错、退出或读取失败 | 原样保留关键错误，说明未完成的验证；不把静态PASS或干净日志说成正常游玩通过 |

截图与pending输入留在 `tools/desktop` 本机，已由该目录 `.gitignore` 排除；公开证据用精简报告和必要结构化结果，不把桌面运行状态当发布资产。

## 独立生产与Git

Blender／DDS重建使用对应模型README和既有构建脚本，不因换智能体重新生成全部资产。离线Blender应后台启动；操作用户打开的Blender前先确认当前场景和任务，避免覆盖其他作品。

Git远程为 `https://github.com/rtgd4652/ppt.git`，开发分支 `knowledge/source-rebuild-v0.1`。用户在2026-10-09明确确认有权并批准上传该次全部251个积累提交，实际已成功；原首次自动审批拒绝已通过明确授权解决。接手只需读取 `git status`／分支／最近提交和必要远端状态，不能把历史“待上传”恢复成现在的阻塞，也不能把原授权泛化为其他仓库、合并或发布。中文提交、无强推、不重写用户历史。

本轮B2安／丽档1正常任务与一次进行态读档已完成，见[首批运行记录](../reports/artifact_growth_batch_b2a_runtime_2026-10-10.md)。随后其余八人的分级核心已接入，启动深度问题已修复；新进程、两页名册及赛斯档1正常调查／公共支援通过，见[第二批续接](../reports/artifact_growth_batch_b2b_2026-10-10.md)。C1随后完成文明科技／制度用途梳理与过时说明修正；无需换智能体后重做旧运行检查。下一包建议为独立的殖民地应急预案，人物组合等待用户决定，高档／替代路径按反馈定向补测。

本批当前档为`2250.09.06.sav`，已正常保存、备份、实际载回并暂停；赛斯任务已结算，原星球奖励235日。能源约9.2万，为用户控制台测试补给；旧`2247.01.25`零能源档只作为首批证据保留，不把它认作当前实时状态。Computer Use已再次完成菜单、法令、通讯、推进／暂停、日期名另存和载回；遇到`user input was detected`先重新观察，截图若实际显示Codex等其他应用则不能操作它，重新识别／置前群星后观察。严禁依据旧截图继续点击，不能自动重放历史补给、战争或剧情命令。

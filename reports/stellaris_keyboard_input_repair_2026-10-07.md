# 群星完整英文自动输入修复 · 2026-10-07

用户要求“什么命令，同时修复自动键盘的问题”，随后手动提交战争前置并确认群星前台准备好。本次修复独立扫描码输入后端，原Computer Use／sky工具未修改。

## 实现与使用

- 脚本：[Send-StellarisText.ps1](/C:/Users/Admin/Desktop/ppt/stellaris-keyboard-input-fix/Send-StellarisText.ps1)。读取单行ASCII文本文件，按目标游戏线程的实际键盘布局映射扫描码，默认每键100ms、间隔80ms；支持完整命令中的Shift标点。
- `Text`只输入，实际截图核对后再用同一文件执行`Submit`。提交核对上次文本、进程、窗口、完成与未提交状态；记录不代替实际画面。
- 目标固定为唯一`F:\steam\steamapps\common\Stellaris\stellaris.exe`窗口。每个新按键前检查前台及身份，失焦停止；不会把命令转发给其他应用。Windows可能拒绝置前，需要用户点击群星。另一屏幕不操作。
- 中文布局与中文／英文输入模式分别判断。首次出现拼音候选，清空输入后只按一次Shift切到英文即成功；不要求安装美式布局。
- 使用方法与证据目录：[README.md](/C:/Users/Admin/Desktop/ppt/stellaris-keyboard-input-fix/README.md)、[HANDOFF.md](/C:/Users/Admin/Desktop/ppt/stellaris-keyboard-input-fix/HANDOFF.md)、[DIAGNOSTICS.md](/C:/Users/Admin/Desktop/ppt/stellaris-keyboard-input-fix/DIAGNOSTICS.md)。原固定help脚本和旧证据保留。

## 实际验证

实际4.5.2（`c7b4`）进程PID3772、窗口593302，布局08040804、Caps Lock关闭；这些是本次值，下一进程重新检查。

1. 连续三次完整help输入和自动回车，均看到帮助列表且输入行清空。
2. 47字符样例`help aemusa_ms.1 "Probe_OK" { root = yes } <= 5`完整显示；只清除，未提交。
3. 73字符日志命令完整显示后自动回车，实际游戏日志17:33:08写入`CC_KEYBOARD_INPUT_OK_1.2`。命令只写日志，不授予资源或写故事状态。
4. 控制台开关实际成功，结束控制台及Debug View均关闭，游戏仍暂停2241.01.25。
5. 日志命令首次发送前失焦，被脚本拒绝且未输入字符；恢复群星前台、核对空行后才重新输入。

同目录`keyboard_20261007_*.png`保留各次真实画面，`keyboard_20261007_game.log`保留当次游戏日志。功能结论来自实际画面与日志，字符映射参考[Microsoft VkKeyScanExW](https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-vkkeyscanexw)和[MapVirtualKeyExW](https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-mapvirtualkeyexw)。

## 边界与Mod续接

已验证群星控制台中的完整英文命令和自动提交，保存名称输入框、中文文本、所有长文本组合及后台输入未测试。没有驻留程序、输入法安装、游戏配置变更或存档覆盖。

此前用户手动的受控战争／敌舰定位已于17:12:54出现`CC_EXILE_TEST_READY`，不要重复执行。M3首批仍需从正常方舟入口发动临时放逐并检查原生MIA实际返回；键盘修复不算该机制通过。共有起点`2241.01.25.sav`、方舟穿界结果`2241.06.05.sav`及此前关键档均保留。

# 群星扫描码输入：单行英文文本与提交分开，原有只读诊断脚本保留。
[CmdletBinding()]
param(
    [ValidateSet('Inspect','Activate','Capture','ShiftMode','ValidateText','Text','ClearText','Submit','ToggleConsole')]
    [string]$Action = 'Inspect',
    [string]$TextFile,
    [ValidateRange(80,300)][int]$HoldMs = 100,
    [ValidateRange(40,300)][int]$GapMs = 80,
    [ValidateRange(0,30000)][int]$WaitForFocusMs = 0,
    # 显式选择同次调用先置前，避免审批/查看截图后下一次调用已失焦；不放宽运行中的守卫。
    [switch]$ActivateFirst,
    # 仅在看图确认拼音模式且输入行清空后显式启用；同次切换并输入，避免两次调用间焦点变化。
    [switch]$ToggleImeBeforeText,
    # 仅在已观察到本轮部分输入时提供长度；默认仍不允许自动清理中断记录。
    [ValidateRange(0,1400)][int]$ObservedPartialLength = 0,
    [ValidatePattern('^[a-zA-Z0-9_-]+$')][string]$Label = 'current'
)
$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Drawing
Add-Type -TypeDefinition @'
using System;
using System.Runtime.InteropServices;
public static class StellarisTextInput {
    [StructLayout(LayoutKind.Sequential)] public struct RECT { public int Left,Top,Right,Bottom; }
    [StructLayout(LayoutKind.Sequential)] public struct KEYBDINPUT { public ushort wVk,wScan; public uint dwFlags,time; public UIntPtr dwExtraInfo; }
    [StructLayout(LayoutKind.Sequential)] public struct MOUSEINPUT { public int dx,dy; public uint mouseData,dwFlags,time; public UIntPtr dwExtraInfo; }
    [StructLayout(LayoutKind.Explicit)] public struct UNION { [FieldOffset(0)] public KEYBDINPUT ki; [FieldOffset(0)] public MOUSEINPUT mi; }
    [StructLayout(LayoutKind.Sequential)] public struct INPUT { public uint type; public UNION data; }
    [DllImport("user32.dll")] public static extern IntPtr GetForegroundWindow();
    [DllImport("user32.dll")] public static extern uint GetWindowThreadProcessId(IntPtr h,out uint pid);
    [DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr h);
    [DllImport("kernel32.dll")] public static extern uint GetCurrentThreadId();
    [DllImport("user32.dll")] public static extern bool AttachThreadInput(uint a,uint b,bool attach);
    [DllImport("user32.dll")] public static extern bool BringWindowToTop(IntPtr h);
    [DllImport("user32.dll")] public static extern bool ShowWindowAsync(IntPtr h,int n);
    [DllImport("user32.dll")] public static extern bool GetWindowRect(IntPtr h,out RECT r);
    [DllImport("user32.dll")] public static extern bool IsIconic(IntPtr h);
    [DllImport("user32.dll")] public static extern IntPtr SetThreadDpiAwarenessContext(IntPtr c);
    [DllImport("user32.dll")] public static extern short GetAsyncKeyState(int k);
    [DllImport("user32.dll")] public static extern short GetKeyState(int k);
    [DllImport("user32.dll")] public static extern IntPtr GetKeyboardLayout(uint thread);
    [DllImport("user32.dll",EntryPoint="VkKeyScanExW",CharSet=CharSet.Unicode)] public static extern short VkKeyScanEx(char ch,IntPtr layout);
    [DllImport("user32.dll",EntryPoint="MapVirtualKeyExW")] public static extern uint MapVirtualKeyEx(uint code,uint mode,IntPtr layout);
    [DllImport("user32.dll",SetLastError=true)] private static extern uint SendInput(uint count,INPUT[] data,int size);
    public static void Key(ushort vk,IntPtr layout,bool up) {
        uint scan=MapVirtualKeyEx(vk,4,layout);
        if(scan==0) throw new InvalidOperationException("No scan code for key.");
        INPUT input=new INPUT(); input.type=1;
        input.data.ki.wScan=(ushort)(scan&0xff);
        input.data.ki.dwFlags=8u|(up?2u:0u)|((scan&0xff00)==0xe000?1u:0u);
        if(SendInput(1,new INPUT[]{input},Marshal.SizeOf(typeof(INPUT)))!=1)
            throw new System.ComponentModel.Win32Exception(Marshal.GetLastWin32Error());
    }
}
'@

# 先检查完整文本，拒绝换行、非ASCII和需要Ctrl/Alt的组合，不发送任何键。
$inputText = $null
$inputPlan = @()
$planLayout = [StellarisTextInput]::GetKeyboardLayout(0)
function New-InputPlan([string]$Value,[IntPtr]$Layout) {
    foreach ($character in $Value.ToCharArray()) {
        $mapping = [int][StellarisTextInput]::VkKeyScanEx($character,$Layout)
        if ($mapping -lt 0 -or (($mapping -shr 8) -band 0xfe) -ne 0) {
            throw ('Unsupported character: '+$character+'; no input sent.')
        }
        [pscustomobject]@{ Key=[ushort]($mapping -band 0xff); Shift=(($mapping -band 0x100) -ne 0) }
    }
}
if ($Action -in @('ValidateText','Text','Submit')) {
    if (-not $TextFile) { throw 'TextFile is required.' }
    $inputText = [IO.File]::ReadAllText((Resolve-Path -LiteralPath $TextFile).Path,[Text.Encoding]::UTF8)
    # 允许文本文件末尾的一个换行，文本本身必须是单行。
    $inputText = $inputText -replace '\r?\n\z',''
    if ($inputText.Length -lt 1 -or $inputText.Length -gt 1400 -or $inputText -match '[^\x20-\x7E]') {
        throw 'Only one non-empty printable ASCII line (max 1400 characters) is accepted.'
    }
    $inputPlan = @(New-InputPlan $inputText $planLayout)
    if ($Action -eq 'ValidateText') {
        [pscustomobject]@{Characters=$inputText.Length;ShiftedCharacters=@($inputPlan | Where-Object Shift).Count;Layout=('{0:X8}' -f ($planLayout.ToInt64() -band 0xffffffffL));Submits=$false} | ConvertTo-Json -Compress
        exit
    }
}

$expectedPath = 'F:\steam\steamapps\common\Stellaris\stellaris.exe'
$games = @(Get-Process -Name stellaris -ErrorAction SilentlyContinue | Where-Object {
    $_.Path -eq $expectedPath -and $_.MainWindowHandle -ne 0
})
if ($games.Count -ne 1) { throw 'Expected one known Stellaris desktop window; no input sent.' }
$game = $games[0]
$gameWindow = $game.MainWindowHandle
[uint32]$ownerPid = 0
$gameThread = [StellarisTextInput]::GetWindowThreadProcessId($gameWindow,[ref]$ownerPid)
$originalLayout = [StellarisTextInput]::GetKeyboardLayout($gameThread)
# 字符映射必须以目标游戏线程布局为准；中文布局的英文模式也可使用。
$planLayout = $originalLayout
if ($Action -in @('Text','Submit')) { $inputPlan = @(New-InputPlan $inputText $planLayout) }
$pendingRecord = Join-Path $PSScriptRoot 'pending-input.json'
function Assert-GameForeground {
    if ([StellarisTextInput]::GetForegroundWindow() -ne $gameWindow) { throw 'Stellaris lost foreground; no new key sent.' }
    [uint32]$currentPid = 0
    [void][StellarisTextInput]::GetWindowThreadProcessId($gameWindow,[ref]$currentPid)
    if ($currentPid -ne $game.Id -or (Get-Process -Id $currentPid).Path -ne $expectedPath) { throw 'Target identity changed.' }
    if ([StellarisTextInput]::IsIconic($gameWindow)) { throw 'Target minimized; no new key sent.' }
}
function Assert-NoPhysicalModifiers {
    foreach ($modifier in @(0x10,0x11,0x12,0x5b,0x5c)) {
        if (([int][StellarisTextInput]::GetAsyncKeyState($modifier) -band 0x8000) -ne 0) { throw 'Modifier held; no new key sent.' }
    }
}
function Save-GameCapture {
    Assert-GameForeground
    $oldDpi = [StellarisTextInput]::SetThreadDpiAwarenessContext([IntPtr](-4))
    try {
        $bounds = New-Object StellarisTextInput+RECT
        if (-not [StellarisTextInput]::GetWindowRect($gameWindow,[ref]$bounds)) { throw 'Cannot read game bounds.' }
        $bitmap = New-Object Drawing.Bitmap(($bounds.Right-$bounds.Left),($bounds.Bottom-$bounds.Top))
        $graphics = [Drawing.Graphics]::FromImage($bitmap)
        try {
            Assert-GameForeground
            $graphics.CopyFromScreen($bounds.Left,$bounds.Top,0,0,$bitmap.Size)
            Assert-GameForeground
            $output = Join-Path $PSScriptRoot ($Label+'.png')
            $bitmap.Save($output,[Drawing.Imaging.ImageFormat]::Png)
            Write-Output ('CAPTURE '+$output)
        } finally { $graphics.Dispose(); $bitmap.Dispose() }
    } finally { [void][StellarisTextInput]::SetThreadDpiAwarenessContext($oldDpi) }
}
function Send-OneKey([ushort]$Key,[bool]$Shift=$false) {
    Assert-GameForeground
    Assert-NoPhysicalModifiers
    $layout = [StellarisTextInput]::GetKeyboardLayout($gameThread)
    if ($Action -in @('Text','Submit') -and $layout -ne $planLayout) { throw 'Game keyboard layout changed; no new key sent.' }
    $shiftDown = $false
    $keyDown = $false
    try {
        if ($Shift) {
            Assert-GameForeground
            [StellarisTextInput]::Key(0xa0,$layout,$false); $shiftDown=$true
            Start-Sleep -Milliseconds 40
        }
        Assert-GameForeground
        [StellarisTextInput]::Key($Key,$layout,$false); $keyDown=$true
        Start-Sleep -Milliseconds $HoldMs
    } finally {
        # 即便失焦也只释放本脚本已经按下的键；不再发新的key-down。
        if ($keyDown) { [StellarisTextInput]::Key($Key,$layout,$true) }
        if ($shiftDown) { [StellarisTextInput]::Key(0xa0,$layout,$true) }
    }
    Assert-GameForeground
    Start-Sleep -Milliseconds $GapMs
}

if ($Action -eq 'Inspect') {
    [uint32]$foregroundPid = 0
    [void][StellarisTextInput]::GetWindowThreadProcessId([StellarisTextInput]::GetForegroundWindow(),[ref]$foregroundPid)
    [pscustomobject]@{Pid=$game.Id;Window=$gameWindow.ToInt64();Foreground=[StellarisTextInput]::GetForegroundWindow().ToInt64();ForegroundPid=$foregroundPid;ForegroundProcess=(Get-Process -Id $foregroundPid -ErrorAction SilentlyContinue).ProcessName;GameLayout=('{0:X8}' -f ($originalLayout.ToInt64() -band 0xffffffffL));CapsLock=(([StellarisTextInput]::GetKeyState(0x14) -band 1) -ne 0)} | ConvertTo-Json -Compress
    exit
}
if ($Action -eq 'Activate' -or $ActivateFirst) {
    if ([StellarisTextInput]::IsIconic($gameWindow)) { [void][StellarisTextInput]::ShowWindowAsync($gameWindow,9) }
    if ([StellarisTextInput]::GetForegroundWindow() -ne $gameWindow) {
        [void][StellarisTextInput]::SetForegroundWindow($gameWindow)
        if ([StellarisTextInput]::GetForegroundWindow() -ne $gameWindow) {
            # 只在显式Activate动作或ActivateFirst请求中临时连接前台线程以恢复游戏焦点；不发送模拟按键。
            # 无论成功或失败都解除连接，之后仍由截图守卫核实真实前台。
            $activationThread = [StellarisTextInput]::GetCurrentThreadId()
            [uint32]$foregroundOwner = 0
            $foregroundThread = [StellarisTextInput]::GetWindowThreadProcessId([StellarisTextInput]::GetForegroundWindow(),[ref]$foregroundOwner)
            $inputAttached = $false
            try {
                if ($foregroundThread -ne 0 -and $foregroundThread -ne $activationThread) {
                    $inputAttached = [StellarisTextInput]::AttachThreadInput($activationThread,$foregroundThread,$true)
                }
                [void][StellarisTextInput]::BringWindowToTop($gameWindow)
                [void][StellarisTextInput]::SetForegroundWindow($gameWindow)
            } finally {
                if ($inputAttached) { [void][StellarisTextInput]::AttachThreadInput($activationThread,$foregroundThread,$false) }
            }
        }
    }
    Start-Sleep -Milliseconds 300
    if ($Action -eq 'Activate') { Save-GameCapture; exit }
    # 组合动作仍逐键检查焦点/进程/物理修饰键，置前失败时在发送前停止。
}
if ($WaitForFocusMs -gt 0) {
    $focusDeadline = [DateTime]::UtcNow.AddMilliseconds($WaitForFocusMs)
    while ([StellarisTextInput]::GetForegroundWindow() -ne $gameWindow -and [DateTime]::UtcNow -lt $focusDeadline) { Start-Sleep -Milliseconds 100 }
}
Assert-GameForeground
if ($Action -eq 'Capture') { Save-GameCapture; exit }
Assert-NoPhysicalModifiers
if ($Action -eq 'Text') {
    if (([StellarisTextInput]::GetKeyState(0x14) -band 1) -ne 0) { throw 'Caps Lock is on; no text sent.' }
    # 失焦后的旧文字仍可能留在游戏输入行；不得覆盖账本并叠加新命令。
    if (Test-Path -LiteralPath $pendingRecord) {
        $previousInput = Get-Content -LiteralPath $pendingRecord -Raw | ConvertFrom-Json
        if (-not $previousInput.Submitted -and $previousInput.Attempted -gt 0) {
            throw 'Unsubmitted text remains; inspect and submit or clear it before typing.'
        }
    }
    if ($ToggleImeBeforeText) {
        # 不把Shift当作英文已成立；文字仍不提交，必须从最终截图核对完整ASCII后另行Submit。
        Send-OneKey 0xa0
        Start-Sleep -Milliseconds 100
    }
    [pscustomobject]@{Pid=$game.Id;Window=$gameWindow.ToInt64();Text=$inputText;Attempted=0;Complete=$false;Submitted=$false} | ConvertTo-Json | Set-Content -LiteralPath $pendingRecord -Encoding utf8
    $attempted = 0
    try {
        foreach ($entry in $inputPlan) {
            Send-OneKey $entry.Key $entry.Shift
            $attempted++
            if (($attempted % 50) -eq 0) { Write-Output ('TEXT_PROGRESS '+$attempted+'/'+$inputPlan.Count) }
        }
    } finally {
        [pscustomobject]@{Pid=$game.Id;Window=$gameWindow.ToInt64();Text=$inputText;Attempted=$attempted;Complete=($attempted -eq $inputPlan.Count);Submitted=$false} | ConvertTo-Json | Set-Content -LiteralPath $pendingRecord -Encoding utf8
    }
} elseif ($Action -eq 'Submit') {
    # Submit只能提交同窗口上一条完整尝试的文本；实际文本仍须先看截图核对。
    if (-not (Test-Path -LiteralPath $pendingRecord)) { throw 'No pending text; no Enter sent.' }
    $pending = Get-Content -LiteralPath $pendingRecord -Raw | ConvertFrom-Json
    if ($pending.Pid -ne $game.Id -or $pending.Window -ne $gameWindow.ToInt64() -or $pending.Text -cne $inputText -or -not $pending.Complete -or $pending.Submitted) { throw 'Pending text does not match; no Enter sent.' }
    Send-OneKey 0x0d
    $pending.Submitted = $true
    $pending | ConvertTo-Json | Set-Content -LiteralPath $pendingRecord -Encoding utf8
} elseif ($Action -eq 'ClearText') {
    if (-not (Test-Path -LiteralPath $pendingRecord)) { throw 'No pending text to clear.' }
    $pending = Get-Content -LiteralPath $pendingRecord -Raw | ConvertFrom-Json
    if ($pending.Pid -ne $game.Id -or $pending.Window -ne $gameWindow.ToInt64() -or $pending.Submitted) { throw 'Pending text not valid for clearing.' }
    $clearCount = $pending.Text.Length
    if (-not $pending.Complete) {
        # 最后一键可能已发送但尚未来得及计数，最多允许一次显式观察到的差值。
        if ($pending.Attempted -lt 1 -or $ObservedPartialLength -lt $pending.Attempted -or
            $ObservedPartialLength -gt ($pending.Attempted + 1) -or $ObservedPartialLength -gt $pending.Text.Length) {
            throw 'Observe the current owned partial text and provide its bounded length; no Backspace sent.'
        }
        $clearCount = $ObservedPartialLength
    }
    # 先依据画面确认光标在自有文字末尾；游戏没有可靠接收 End 键。
    for ($index=0; $index -lt $clearCount; $index++) { Send-OneKey 0x08 }
    $pending.Complete = $false
    $pending.Attempted = 0
    $pending | ConvertTo-Json | Set-Content -LiteralPath $pendingRecord -Encoding utf8
} elseif ($Action -eq 'ShiftMode') {
    # 仅在已确认输入行空白时切换一次，随后核对实际英文输入，不重复历史help排障。
    Send-OneKey 0xa0
} elseif ($Action -eq 'ToggleConsole') {
    Send-OneKey 0xc0
}
Start-Sleep -Milliseconds 250
Save-GameCapture
Write-Output ('INPUT_ATTEMPT action='+$Action+'; actual game receipt must be verified in screenshot/log')

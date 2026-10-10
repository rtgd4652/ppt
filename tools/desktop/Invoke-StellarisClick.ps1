# 群星窗口内单次点击：必须依据刚刚查看的原尺寸截图，不提供后台输入或自动置前。
[CmdletBinding()]
param(
    [Parameter(Mandatory)][ValidateRange(0.0,1.0)][double]$X,
    [Parameter(Mandatory)][ValidateRange(0.0,1.0)][double]$Y,
    [Parameter(Mandatory)][string]$ReferenceImage,
    [Parameter(Mandatory)][ValidateRange(1,2147483647)][int]$ExpectedGameProcessId
)
$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Drawing
Add-Type -TypeDefinition @'
using System;
using System.Runtime.InteropServices;
public static class StellarisWindowClick {
    [StructLayout(LayoutKind.Sequential)] public struct RECT { public int Left,Top,Right,Bottom; }
    [StructLayout(LayoutKind.Sequential)] public struct POINT { public int X,Y; }
    [StructLayout(LayoutKind.Sequential)] public struct MOUSEINPUT { public int dx,dy; public uint mouseData,dwFlags,time; public UIntPtr dwExtraInfo; }
    [StructLayout(LayoutKind.Sequential)] public struct INPUT { public uint type; public MOUSEINPUT data; }
    [DllImport("user32.dll")] public static extern IntPtr GetForegroundWindow();
    [DllImport("user32.dll")] public static extern bool GetWindowRect(IntPtr window,out RECT bounds);
    [DllImport("user32.dll")] public static extern bool GetClientRect(IntPtr window,out RECT bounds);
    [DllImport("user32.dll")] public static extern bool ClientToScreen(IntPtr window,ref POINT point);
    [DllImport("user32.dll")] public static extern bool IsIconic(IntPtr window);
    [DllImport("user32.dll")] public static extern short GetAsyncKeyState(int key);
    [DllImport("user32.dll")] public static extern IntPtr SetThreadDpiAwarenessContext(IntPtr context);
    [DllImport("user32.dll",SetLastError=true)] public static extern bool SetCursorPos(int x,int y);
    [DllImport("user32.dll",SetLastError=true)] private static extern uint SendInput(uint count,INPUT[] inputs,int size);
    public static void LeftButton(bool up) {
        INPUT input=new INPUT(); input.type=0; input.data.dwFlags=up?4u:2u;
        if(SendInput(1,new INPUT[]{input},Marshal.SizeOf(typeof(INPUT)))!=1)
            throw new System.ComponentModel.Win32Exception(Marshal.GetLastWin32Error());
    }
}
'@
$knownExecutable = 'F:\steam\steamapps\common\Stellaris\stellaris.exe'
$candidateGames = @(Get-Process -Name stellaris -ErrorAction SilentlyContinue | Where-Object {
    $_.Path -eq $knownExecutable -and $_.MainWindowHandle -ne 0
})
if ($candidateGames.Count -ne 1 -or $candidateGames[0].Id -ne $ExpectedGameProcessId) {
    throw 'Expected current unique Stellaris process; no pointer input sent.'
}
$targetGame = $candidateGames[0]
$targetWindow = $targetGame.MainWindowHandle
function Assert-CurrentGame {
    $currentGame = Get-Process -Id $ExpectedGameProcessId -ErrorAction Stop
    if ($currentGame.Path -ne $knownExecutable -or $currentGame.MainWindowHandle -ne $targetWindow -or
        [StellarisWindowClick]::GetForegroundWindow() -ne $targetWindow -or
        [StellarisWindowClick]::IsIconic($targetWindow)) {
        throw 'Game identity or foreground changed; no new mouse-down sent.'
    }
    foreach ($physicalKey in @(0x10,0x11,0x12,0x5b,0x5c)) {
        if (([int][StellarisWindowClick]::GetAsyncKeyState($physicalKey) -band 0x8000) -ne 0) {
            throw 'Physical modifier held; no new mouse-down sent.'
        }
    }
}
Assert-CurrentGame
if (([int][StellarisWindowClick]::GetAsyncKeyState(0x01) -band 0x8000) -ne 0) {
    throw 'Left mouse button already held; no pointer input sent.'
}
$referenceFile = Get-Item -LiteralPath $ReferenceImage -ErrorAction Stop
if (([DateTime]::UtcNow - $referenceFile.LastWriteTimeUtc).TotalSeconds -gt 120) {
    throw 'Reference capture is older than 120 seconds; capture and inspect the current game first.'
}
$oldDpiContext = [StellarisWindowClick]::SetThreadDpiAwarenessContext([IntPtr](-4))
try {
    $windowBounds = New-Object StellarisWindowClick+RECT
    $clientBounds = New-Object StellarisWindowClick+RECT
    $clientOrigin = New-Object StellarisWindowClick+POINT
    if (-not [StellarisWindowClick]::GetWindowRect($targetWindow,[ref]$windowBounds) -or
        -not [StellarisWindowClick]::GetClientRect($targetWindow,[ref]$clientBounds) -or
        -not [StellarisWindowClick]::ClientToScreen($targetWindow,[ref]$clientOrigin)) {
        throw 'Cannot read current game bounds; no pointer input sent.'
    }
    $referenceBitmap = [Drawing.Image]::FromFile($referenceFile.FullName)
    try {
        if ($referenceBitmap.Width -ne ($windowBounds.Right-$windowBounds.Left) -or
            $referenceBitmap.Height -ne ($windowBounds.Bottom-$windowBounds.Top)) {
            throw 'Window dimensions differ from reference capture; no pointer input sent.'
        }
    } finally { $referenceBitmap.Dispose() }
    $clickX = $windowBounds.Left + [int][Math]::Round($X * ($windowBounds.Right-$windowBounds.Left-1))
    $clickY = $windowBounds.Top + [int][Math]::Round($Y * ($windowBounds.Bottom-$windowBounds.Top-1))
    if ($clickX -lt $clientOrigin.X -or $clickX -ge ($clientOrigin.X+$clientBounds.Right) -or
        $clickY -lt $clientOrigin.Y -or $clickY -ge ($clientOrigin.Y+$clientBounds.Bottom)) {
        throw 'Point is outside the game client area; no pointer input sent.'
    }
    Assert-CurrentGame
    if (-not [StellarisWindowClick]::SetCursorPos($clickX,$clickY)) { throw 'Cannot place pointer inside game.' }
    Start-Sleep -Milliseconds 80
    Assert-CurrentGame
    $buttonDown = $false
    try {
        [StellarisWindowClick]::LeftButton($false)
        $buttonDown = $true
        Start-Sleep -Milliseconds 100
    } finally {
        # 只释放本脚本按下的按钮，失焦时不再发送新的按下操作。
        if ($buttonDown) { [StellarisWindowClick]::LeftButton($true) }
    }
    Start-Sleep -Milliseconds 250
    Assert-CurrentGame
    [pscustomobject]@{Pid=$targetGame.Id;Window=$targetWindow.ToInt64();X=$clickX;Y=$clickY;Attempted=$true} | ConvertTo-Json -Compress
    Write-Output 'Click attempted; capture the game and verify the actual result.'
} finally {
    [void][StellarisWindowClick]::SetThreadDpiAwarenessContext($oldDpiContext)
}

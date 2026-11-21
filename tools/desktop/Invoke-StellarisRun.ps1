# 在同一次调用内短段运行并确认暂停，避免模型查看截图期间游戏持续推进。
# 沿用既有鼠标、焦点、窗口身份和暂停图标守卫；任何无法确认的状态都报错。
[CmdletBinding()]
param(
    [Parameter(Mandatory)][ValidateRange(1,2147483647)][int]$ExpectedGameProcessId,
    [Parameter(Mandatory)][string]$IsolatedProfilePath,
    [ValidateRange(1,20)][int]$Seconds = 2,
    [ValidatePattern('^[a-z0-9_]{1,50}$')][string]$Label = 'bounded_run'
)
$ErrorActionPreference = 'Stop'
$repoRoot = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$tempRoot = [IO.Path]::GetFullPath((Join-Path $repoRoot 'temp')).TrimEnd('\') + '\'
$resolvedTestProfile = (Resolve-Path -LiteralPath $IsolatedProfilePath).Path
if (-not (Test-Path -LiteralPath $resolvedTestProfile -PathType Container) -or
    -not $resolvedTestProfile.StartsWith($tempRoot,[StringComparison]::OrdinalIgnoreCase)) {
    throw 'Run control only accepts an existing isolated profile below this repository temp directory.'
}
$process = Get-CimInstance Win32_Process -Filter "ProcessId=$ExpectedGameProcessId"
# Windows 启动器可能引用整个参数，也可能只引用路径。只接受完整的 userdir 参数。
$profileMatch = [regex]::Match([string]$process.CommandLine,'(?i)(?:^|\s)(?:"--?userdir=(?<path>[^"]+)"|--?userdir(?:=|\s+)(?:"(?<path>[^"]+)"|(?<path>[^\s"]+)))(?=\s|$)')
$actualProfile = $profileMatch.Groups['path'].Value
if (-not $process -or $process.ExecutablePath -ne 'F:\steam\steamapps\common\Stellaris\stellaris.exe' -or
    -not $profileMatch.Success -or $actualProfile.TrimEnd('/','\').Replace('\','/') -ine $resolvedTestProfile.TrimEnd('/','\').Replace('\','/')) {
    throw 'Process is not the requested isolated Stellaris instance; no input sent.'
}
$capture = Join-Path $PSScriptRoot 'Send-StellarisText.ps1'
$click = Join-Path $PSScriptRoot 'Invoke-StellarisClick.ps1'
$reference = Join-Path $PSScriptRoot ('before_' + $Label + '.png')
& $capture -Action Capture -ActivateFirst -WaitForFocusMs 3000 -Label ('before_' + $Label)
$attempted = $false
try {
    # 300秒模式也会在发送前检查游戏确实暂停；不把现有运行状态反向切换。
    # 在调用前标记尝试，确保“输入可能已发出但随后报错”也进入暂停清理。
    $attempted = $true
    & $click -ExpectedGameProcessId $ExpectedGameProcessId -ReferenceImage $reference -X .900 -Y .043 -MaxReferenceAgeSeconds 300
    Start-Sleep -Seconds $Seconds
} finally {
    if ($attempted) {
        & $click -ExpectedGameProcessId $ExpectedGameProcessId -ReferenceImage $reference -X .900 -Y .043 -EnsurePaused
        # 等界面稳定后再次只读判定；如果事件已经暂停，不再点击以免恢复运行。
        Start-Sleep -Milliseconds 750
        & $click -ExpectedGameProcessId $ExpectedGameProcessId -ReferenceImage $reference -X .900 -Y .043 -EnsurePaused
        & $capture -Action Capture -Label ('after_' + $Label)
    }
}
[pscustomobject]@{
    Pid = $ExpectedGameProcessId
    Profile = $resolvedTestProfile
    RequestedSeconds = $Seconds
    PauseConfirmed = $true
    Capture = (Join-Path $PSScriptRoot ('after_' + $Label + '.png'))
} | ConvertTo-Json -Compress

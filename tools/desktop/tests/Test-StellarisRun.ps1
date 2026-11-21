# 在隔离假目录执行真实运行控制器，模拟其鼠标与进程边界；不加载Win32、不发送桌面输入。
$ErrorActionPreference = 'Stop'
$repoRoot = Split-Path -Parent (Split-Path -Parent (Split-Path -Parent $PSScriptRoot))
$testRoot = Join-Path $repoRoot 'temp\desktop_run_guard_checks'
$fakeDesktop = Join-Path $testRoot 'tools\desktop'
$fakeProfile = Join-Path $testRoot 'temp\profile'
$outsideProfile = Join-Path $testRoot 'outside'
[void](New-Item -ItemType Directory -Path $fakeDesktop,$fakeProfile,$outsideProfile -Force)
Copy-Item -LiteralPath (Join-Path $PSScriptRoot '..\Invoke-StellarisRun.ps1') -Destination (Join-Path $fakeDesktop 'Invoke-StellarisRun.ps1')
@'
param($Action,[switch]$ActivateFirst,$WaitForFocusMs,$Label)
[void]$global:StellarisRunTestState.Captures.Add($Label)
'@ | Set-Content -LiteralPath (Join-Path $fakeDesktop 'Send-StellarisText.ps1') -Encoding utf8
@'
param($ExpectedGameProcessId,$ReferenceImage,$X,$Y,$MaxReferenceAgeSeconds,[switch]$EnsurePaused)
$s=$global:StellarisRunTestState
if ($EnsurePaused) {
    $s.PauseChecks++
    if ($s.FailPause) { throw 'simulated focus loss during pause' }
    if (-not $s.Paused) { $s.PauseClicks++; $s.Paused=$true }
} else {
    if (-not $s.Paused) { throw 'start requires paused state' }
    $s.StartClicks++; $s.Paused=$false
    if ($s.FailStart) { throw 'simulated exception after input' }
}
'@ | Set-Content -LiteralPath (Join-Path $fakeDesktop 'Invoke-StellarisClick.ps1') -Encoding utf8
function Get-CimInstance {
    param($ClassName,$Filter)
    # 覆盖启动器引用整个参数和只引用路径的两种真实 Windows 启动形式。
    $profileValue = $fakeProfile.Replace('\','/')
    $userdirArg = switch ($global:StellarisRunTestState.ProfileForm) {
        'quoted_argument' { '"-userdir=' + $profileValue + '"' }
        'wrong_profile'   { '"-userdir=' + $profileValue + '-other"' }
        default           { '-userdir="' + $profileValue + '"' }
    }
    [pscustomobject]@{
        ExecutablePath = if ($global:StellarisRunTestState.BadIdentity) { 'wrong.exe' } else { 'F:\steam\steamapps\common\Stellaris\stellaris.exe' }
        CommandLine = '"F:\steam\steamapps\common\Stellaris\stellaris.exe" ' + $userdirArg + ' --continuelastsave'
    }
}
function Start-Sleep {
    param($Seconds,$Milliseconds)
    if ($Seconds -and $global:StellarisRunTestState.AutoPause) { $global:StellarisRunTestState.Paused=$true }
    if ($Seconds -and $global:StellarisRunTestState.FailSleep) { throw 'simulated wait interruption' }
}
$cases = @(
    @{Name='normal'; Fail=$false; Start=1; Pause=1},
    @{Name='event_already_paused'; AutoPause=$true; Fail=$false; Start=1; Pause=0},
    @{Name='error_after_input'; FailStart=$true; Fail=$true; Start=1; Pause=1},
    @{Name='wait_interrupted'; FailSleep=$true; Fail=$true; Start=1; Pause=1},
    @{Name='cannot_confirm_pause'; FailPause=$true; Fail=$true; Start=1; Pause=0},
    @{Name='quoted_userdir_argument'; ProfileForm='quoted_argument'; Fail=$false; Start=1; Pause=1},
    @{Name='different_quoted_profile'; ProfileForm='wrong_profile'; Fail=$true; Start=0; Pause=0},
    @{Name='wrong_game'; BadIdentity=$true; Fail=$true; Start=0; Pause=0},
    @{Name='outside_profile'; Outside=$true; Fail=$true; Start=0; Pause=0}
)
foreach ($case in $cases) {
    $global:StellarisRunTestState = [pscustomobject]@{
        Paused=$true; StartClicks=0; PauseClicks=0; PauseChecks=0
        Captures=[Collections.Generic.List[string]]::new()
        AutoPause=[bool]$case.AutoPause; FailStart=[bool]$case.FailStart
        FailSleep=[bool]$case.FailSleep; FailPause=[bool]$case.FailPause
        ProfileForm=$case.ProfileForm; BadIdentity=[bool]$case.BadIdentity
    }
    $requestedProfile = if ($case.Outside) { $outsideProfile } else { $fakeProfile }
    $failed=$false; $result=@()
    try {
        $result=@(& (Join-Path $fakeDesktop 'Invoke-StellarisRun.ps1') -ExpectedGameProcessId 123 -IsolatedProfilePath $requestedProfile -Seconds 2)
    } catch { $failed=$true }
    $s=$global:StellarisRunTestState
    if ($failed -ne $case.Fail -or $s.StartClicks -ne $case.Start -or $s.PauseClicks -ne $case.Pause) { throw ('Unexpected outcome: '+$case.Name) }
    if (-not $case.Fail) {
        $receipt=$result[-1] | ConvertFrom-Json
        if (-not $receipt.PauseConfirmed -or -not $s.Paused -or $s.PauseChecks -ne 2) { throw ('Pause not confirmed: '+$case.Name) }
    } elseif (@($result | Where-Object { $_ -match '"PauseConfirmed":true' }).Count) {
        throw ('Failed operation claimed success: '+$case.Name)
    }
    if ($case.Start -eq 0 -and $s.Captures.Count -gt 0) { throw ('Rejected identity reached GUI boundary: '+$case.Name) }
}
Write-Output ('通过 '+$cases.Count+' 项运行控制器行为检查；未读取或操作桌面。')

# 仅执行正式脚本的清理分支，模拟按键出口；不读取桌面、不加载Win32、不发送真实输入。
$ErrorActionPreference = 'Stop'
$source = Join-Path $PSScriptRoot '..\Send-StellarisText.ps1'
$tokens = $null
$parseErrors = $null
$ast = [System.Management.Automation.Language.Parser]::ParseFile((Resolve-Path -LiteralPath $source).Path,[ref]$tokens,[ref]$parseErrors)
if ($parseErrors.Count -gt 0) { throw 'Desktop script has syntax errors.' }
$branches = @(
    foreach ($node in $ast.FindAll({ param($n) $n -is [System.Management.Automation.Language.IfStatementAst] },$true)) {
        foreach ($clause in $node.Clauses) {
            if ($clause.Item1.Extent.Text -eq '$Action -eq ''ClearText''') { $clause.Item2 }
        }
    }
)
if ($branches.Count -ne 1) { throw 'Expected one actual ClearText branch.' }
$body = $branches[0].Extent.Text
$clear = [scriptblock]::Create($body.Substring(1,$body.Length-2))
$pendingRecord = Join-Path ([IO.Path]::GetTempPath()) ('StellarisTextClearing-'+[Guid]::NewGuid().ToString('N')+'.json')
$game = [pscustomobject]@{ Id = 22680 }
$gameWindow = [IntPtr]526698
$script:sentKeys = [Collections.Generic.List[int]]::new()
function Send-OneKey([ushort]$Key) { [void]$script:sentKeys.Add($Key) }
$cases = @(
    @{ Name='complete'; Complete=$true; Attempted=6; Observed=0; Pid=22680; Window=526698; Submitted=$false; Expected=6 },
    @{ Name='observed_partial'; Complete=$false; Attempted=3; Observed=3; Pid=22680; Window=526698; Submitted=$false; Expected=3 },
    @{ Name='observed_last_key'; Complete=$false; Attempted=3; Observed=4; Pid=22680; Window=526698; Submitted=$false; Expected=4 },
    @{ Name='unobserved_partial'; Complete=$false; Attempted=3; Observed=0; Pid=22680; Window=526698; Submitted=$false; Expected=-1 },
    @{ Name='excess_length'; Complete=$false; Attempted=3; Observed=5; Pid=22680; Window=526698; Submitted=$false; Expected=-1 },
    @{ Name='different_process'; Complete=$false; Attempted=3; Observed=3; Pid=111; Window=526698; Submitted=$false; Expected=-1 },
    @{ Name='different_window'; Complete=$false; Attempted=3; Observed=3; Pid=22680; Window=111; Submitted=$false; Expected=-1 },
    @{ Name='already_submitted'; Complete=$false; Attempted=3; Observed=3; Pid=22680; Window=526698; Submitted=$true; Expected=-1 },
    @{ Name='no_attempt'; Complete=$false; Attempted=0; Observed=1; Pid=22680; Window=526698; Submitted=$false; Expected=-1 }
)
try {
    foreach ($case in $cases) {
        $pending = [pscustomobject]@{ Pid=$case.Pid; Window=$case.Window; Text='abcdef'; Attempted=$case.Attempted; Complete=$case.Complete; Submitted=$case.Submitted }
        $pending | ConvertTo-Json | Set-Content -LiteralPath $pendingRecord -Encoding utf8
        $ObservedPartialLength = $case.Observed
        $script:sentKeys.Clear()
        $failed = $false
        try { & $clear } catch { $failed = $true }
        if ($case.Expected -lt 0) {
            if (-not $failed -or $script:sentKeys.Count -ne 0) { throw ('Unsafe branch: '+$case.Name) }
        } else {
            if ($failed -or $script:sentKeys.Count -ne $case.Expected -or @($script:sentKeys | Where-Object { $_ -ne 8 }).Count -gt 0) { throw ('Wrong clear: '+$case.Name) }
            $after = Get-Content -LiteralPath $pendingRecord -Raw | ConvertFrom-Json
            if ($after.Attempted -ne 0 -or $after.Complete -or $after.Submitted) { throw ('Wrong receipt: '+$case.Name) }
        }
    }
    Write-Output ('通过 '+$cases.Count+' 项源码守卫检查；未发送桌面输入。')
} finally {
    if (Test-Path -LiteralPath $pendingRecord) { Remove-Item -LiteralPath $pendingRecord }
}

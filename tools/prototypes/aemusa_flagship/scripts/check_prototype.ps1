$ErrorActionPreference = "Stop"

$ScriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$PrototypeRoot = Split-Path -Parent $ScriptRoot
$SkeletonRoot = Join-Path $PrototypeRoot "mod_skeleton"
$Errors = New-Object System.Collections.Generic.List[string]
$Warnings = New-Object System.Collections.Generic.List[string]

# 原型闭环必须具备的最小文件集合。
$RequiredFiles = @(
    "descriptor.mod",
    "common/ship_sizes/aemusa_fp_ship_size.txt",
    "common/section_templates/aemusa_fp_sections.txt",
    "common/component_templates/aemusa_fp_components.txt",
    "common/scripted_effects/aemusa_fp_effects.txt",
    "common/on_actions/aemusa_fp_on_actions.txt",
    "common/situations/aemusa_fp_situations.txt",
    "events/aemusa_fp_events.txt",
    "localisation/simp_chinese/aemusa_fp_l_simp_chinese.yml"
)

foreach ($RelativePath in $RequiredFiles) {
    $Path = Join-Path $SkeletonRoot $RelativePath
    if (-not (Test-Path -LiteralPath $Path)) {
        $Errors.Add("缺失文件：$RelativePath")
    }
}

# 非本地化脚本必须无 BOM；简体中文本地化必须保留 UTF-8 BOM。
$ScriptFiles = Get-ChildItem -LiteralPath $SkeletonRoot -Recurse -File | Where-Object {
    $_.Extension -in @(".txt", ".mod")
}
foreach ($File in $ScriptFiles) {
    $Bytes = [System.IO.File]::ReadAllBytes($File.FullName)
    if ($Bytes.Length -ge 3 -and $Bytes[0] -eq 0xEF -and $Bytes[1] -eq 0xBB -and $Bytes[2] -eq 0xBF) {
        $Errors.Add("非本地化文件带 UTF-8 BOM：$($File.FullName)")
    }

    # 去掉井号注释后进行轻量花括号计数；实机加载仍是最终语法验证。
    $Text = [System.IO.File]::ReadAllText($File.FullName)
    $WithoutComments = ($Text -split "`r?`n" | ForEach-Object { ($_ -replace '#.*$', '') }) -join "`n"
    $OpenCount = ([regex]::Matches($WithoutComments, '\{')).Count
    $CloseCount = ([regex]::Matches($WithoutComments, '\}')).Count
    if ($OpenCount -ne $CloseCount) {
        $Errors.Add("花括号不匹配：$($File.FullName)（$OpenCount/$CloseCount）")
    }
}

$LocFile = Join-Path $SkeletonRoot "localisation/simp_chinese/aemusa_fp_l_simp_chinese.yml"
if (Test-Path -LiteralPath $LocFile) {
    $LocBytes = [System.IO.File]::ReadAllBytes($LocFile)
    $HasBom = $LocBytes.Length -ge 3 -and $LocBytes[0] -eq 0xEF -and $LocBytes[1] -eq 0xBB -and $LocBytes[2] -eq 0xBF
    if (-not $HasBom) {
        $Errors.Add("简体中文本地化缺少 UTF-8 BOM：$LocFile")
    }
}

# 检查原型前缀和已知无效资源键，降低污染正式命名空间的风险。
$AllText = (Get-ChildItem -LiteralPath $SkeletonRoot -Recurse -File | ForEach-Object {
    [System.IO.File]::ReadAllText($_.FullName)
}) -join "`n"
if ($AllText -match '\btrade_value\s*=') {
    $Errors.Add("发现无效资源键 trade_value")
}
if ($AllText -notmatch 'namespace\s*=\s*aemusa_fp') {
    $Errors.Add("缺少 aemusa_fp 事件命名空间")
}
if ($AllText -notmatch 'jumpdrive\s*=\s*yes') {
    $Errors.Add("原型跃迁核心缺少 jumpdrive = yes")
}

# 多设计精确恢复仍是开放验证项，静态检查必须持续提醒而不能误报为完成。
$Warnings.Add("多份同舰种设计下的精确恢复尚需实机验证。")
$Warnings.Add("玩家手动合并舰队无法由已验证的通用字段禁止。")

foreach ($Warning in $Warnings) {
    Write-Warning $Warning
}

if ($Errors.Count -gt 0) {
    foreach ($ErrorMessage in $Errors) {
        Write-Error $ErrorMessage
    }
    exit 1
}

Write-Host "隔离原型静态检查通过。"
Write-Host "注意：仍需 Stellaris 4.4.3 新开局与 error.log 实机验收。"

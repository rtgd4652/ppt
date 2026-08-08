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
    "common/global_ship_designs/aemusa_fp_global_designs.txt",
    "common/component_templates/aemusa_fp_components.txt",
    "common/static_modifiers/aemusa_fp_static_modifiers.txt",
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

# 部署锁定不能再次退回会隐藏舰船的 set_disabled；当前候选必须包含单链命令监视器。
if ($AllText -notmatch 'id\s*=\s*aemusa_fp\.21' -or $AllText -notmatch 'clear_orders\s*=\s*yes') {
    $Errors.Add("部署锁定缺少 aemusa_fp.21 命令监视器或 clear_orders")
}
if ($AllText -match 'aemusa_fp\.20\.deploy[\s\S]{0,1200}set_disabled\s*=\s*yes') {
    $Errors.Add("部署入口重新使用 set_disabled，会导致原舰从正常界面消失")
}
if ($AllText -match '(any|every|random|count)_owned_ship') {
    $Errors.Add("旗舰生命周期仍在使用 owned_ship；特殊军事舰必须统一按 controlled_ship 识别")
}

# 舰队必须拥有明确的星系内位置，否则引擎会将其强制送入失踪返航。
if ($AllText -notmatch 'set_location\s*=\s*\{') {
    $Errors.Add("原型生成效果缺少明确 set_location，舰队可能被判定为星系外失踪")
}

# 隔离原型固定使用已存在实体，禁止再次按图形文化拼接不存在的自定义舰种实体名。
if ($AllText -notmatch 'graphical_culture\s*=\s*no') {
    $Errors.Add("原型舰种未关闭图形文化实体拼接")
}

# 方案 B 必须使用固定预制型，禁止重新引入随机玩家设计选择。
if ($AllText -match 'random_owned_design') {
    $Errors.Add("方案 B 不得使用 random_owned_design")
}
if ($AllText -notmatch 'design\s*=\s*"NAME_AEMUSA_FP_PRESET_DESIGN_V2"') {
    $Errors.Add("方案 B 生成效果没有引用 V2 固定预制设计")
}
if ($AllText -match 'allow_buildable_trigger\s*=\s*\{') {
    $Errors.Add("全局舰船设计不得把 allow_buildable_trigger 写成内联触发块")
}
if ($AllText -notmatch 'set_country_flag\s*=\s*aemusa_fp_spawn_failed') {
    $Errors.Add("生成效果缺少失败账本标记，可能把空实例误报为现役")
}
if ($AllText -notmatch 'name\s*=\s*aemusa_fp\.10\.recover') {
    $Errors.Add("人工审计缺少既有事务恢复入口")
}
if ($AllText -notmatch 'aemusa_fp_adopt_single_unmarked_candidate_effect') {
    $Errors.Add("缺失恢复没有接管唯一无标记候选舰")
}
if ($AllText -notmatch 'count_controlled_ship\s*=\s*\{\s*count\s*=\s*1\s*limit\s*=\s*\{\s*is_ship_size\s*=\s*aemusa_fp_flagship') {
    $Errors.Add("旧存档恢复没有按唯一原型舰种识别候选舰")
}
if ($AllText -notmatch 'id\s*=\s*aemusa_fp\.11') {
    $Errors.Add("缺少绕过界面选项条件的独立旧存档恢复事件")
}
if ($AllText -notmatch 'id\s*=\s*aemusa_fp\.12') {
    $Errors.Add("缺少解除旧版 set_disabled 状态的安全救援事件")
}
if ($AllText -match 'set_disabled\s*=\s*yes') {
    $Errors.Add("部署锁定不得继续使用 set_disabled = yes 隐藏旗舰")
}
if ($AllText -notmatch 'aemusa_fp_deployment_lock\s*=\s*\{[\s\S]*?ship_speed_mult\s*=\s*-1') {
    $Errors.Add("缺少非隐藏部署锁定静态修正")
}
if ($AllText -notmatch 'last_created_ship\s*=\s*\{[\s\S]*?set_ship_flag\s*=\s*aemusa_fp_unique_flagship') {
    $Errors.Add("旗舰生成后没有通过 last_created_ship 写入唯一身份标记")
}
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

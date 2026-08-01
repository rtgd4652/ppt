param(
    [string]$OutputRoot = ""
)

$ErrorActionPreference = "Stop"

# 只允许把组装产物写入本原型目录，避免误覆盖正式 Mod 或用户文档目录。
$ScriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$PrototypeRoot = Split-Path -Parent $ScriptRoot
$SkeletonRoot = Join-Path $PrototypeRoot "mod_skeleton"
$DefaultBuildRoot = Join-Path $PrototypeRoot "build"

if ([string]::IsNullOrWhiteSpace($OutputRoot)) {
    $OutputRoot = $DefaultBuildRoot
}

$ResolvedPrototype = [System.IO.Path]::GetFullPath($PrototypeRoot)
$ResolvedOutput = [System.IO.Path]::GetFullPath($OutputRoot)
if (-not $ResolvedOutput.StartsWith($ResolvedPrototype, [System.StringComparison]::OrdinalIgnoreCase)) {
    throw "拒绝写入原型目录之外：$ResolvedOutput"
}

$ModFolder = Join-Path $ResolvedOutput "AemusaFlagshipPrototype"
if (Test-Path -LiteralPath $ModFolder) {
    # 删除前再次验证最终目标仍位于原型 build 目录内。
    $ResolvedModFolder = [System.IO.Path]::GetFullPath($ModFolder)
    if (-not $ResolvedModFolder.StartsWith($ResolvedPrototype, [System.StringComparison]::OrdinalIgnoreCase)) {
        throw "拒绝清理原型目录之外：$ResolvedModFolder"
    }
    Remove-Item -LiteralPath $ModFolder -Recurse -Force
}

New-Item -ItemType Directory -Path $ModFolder -Force | Out-Null
Copy-Item -Path (Join-Path $SkeletonRoot "*") -Destination $ModFolder -Recurse -Force

# 侧边描述符使用无 BOM UTF-8；path 仅描述手工安装后的相对目录名。
$SidecarPath = Join-Path $ResolvedOutput "aemusa_flagship_prototype.mod"
$Sidecar = @"
name="爱缪莎旗舰技术原型"
version="0.0.1-prototype"
path="mod/AemusaFlagshipPrototype"
tags={
    "Gameplay"
    "Utilities"
}
supported_version="4.4.*"
"@
[System.IO.File]::WriteAllText($SidecarPath, $Sidecar, [System.Text.UTF8Encoding]::new($false))

Write-Host "原型已组装：$ModFolder"
Write-Host "侧边描述符：$SidecarPath"
Write-Host "未修改正式 mod/，也未自动安装到用户目录。"

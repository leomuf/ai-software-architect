# SPDX-FileCopyrightText: 2026 Leonardo Muffato (AUTOSOFT Engineering - www.autosoft-engineering.de)
# SPDX-License-Identifier: MIT

#Requires -Version 5.1

<#
.SYNOPSIS
Copies a validated development package into the default personal marketplace.

.DESCRIPTION
Validates the source package and the exact personal-marketplace catalog entry,
then performs a staged replacement with rollback. It never edits marketplace.json
or Codex's installed-plugin cache. Installation or update remains a user action in
the Codex Plugins window.

.PARAMETER PluginPath
Plugin package to copy. Relative paths are resolved from the repository root.

.EXAMPLE
.\scripts\copy-codex-plugin-to-personal-marketplace.ps1 -WhatIf

.EXAMPLE
.\scripts\copy-codex-plugin-to-personal-marketplace.ps1
#>

[CmdletBinding(SupportsShouldProcess = $true, ConfirmImpact = "Medium")]
param(
    [string]$PluginPath = "dist\codex\ai-software-architect"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$PluginName = "ai-software-architect"
$ExpectedSourcePath = "./plugins/ai-software-architect"
$RepositoryRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot ".."))
$ValidatorProgram = Join-Path $RepositoryRoot "adapters\codex\validate_plugin.py"
$RepositoryUvCache = Join-Path $RepositoryRoot ".uv-cache"
$MarketplaceRoot = Join-Path ([Environment]::GetFolderPath("UserProfile")) ".agents\plugins"
$MarketplaceFile = Join-Path $MarketplaceRoot "marketplace.json"
$TargetParent = [IO.Path]::GetFullPath((Join-Path $MarketplaceRoot "plugins"))
$Target = [IO.Path]::GetFullPath((Join-Path $TargetParent $PluginName))

function Invoke-Checked {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Command,

        [Parameter(Mandatory = $true)]
        [string[]]$Arguments
    )

    & $Command @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "Command failed with exit code ${LASTEXITCODE}: $Command"
    }
}

function Test-SamePath {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Left,

        [Parameter(Mandatory = $true)]
        [string]$Right
    )

    return [StringComparer]::OrdinalIgnoreCase.Equals(
        [IO.Path]::GetFullPath($Left).TrimEnd("\"),
        [IO.Path]::GetFullPath($Right).TrimEnd("\")
    )
}

function Assert-ManagedTemporaryPath {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Path
    )

    $FullPath = [IO.Path]::GetFullPath($Path)
    if (-not (Test-SamePath (Split-Path -Parent $FullPath) $TargetParent)) {
        throw "Refusing temporary path outside the marketplace plugin directory: $FullPath"
    }
    if ((Split-Path -Leaf $FullPath) -notlike ".$PluginName.*") {
        throw "Refusing unexpected temporary marketplace path: $FullPath"
    }
}

if ([IO.Path]::IsPathRooted($PluginPath)) {
    $RequestedSource = $PluginPath
}
else {
    $RequestedSource = Join-Path $RepositoryRoot $PluginPath
}
$Source = (Resolve-Path -LiteralPath $RequestedSource -ErrorAction Stop).Path
if (-not (Test-Path -LiteralPath $Source -PathType Container)) {
    throw "Plugin package not found: $Source"
}

if (-not (Test-SamePath (Split-Path -Parent $Target) $TargetParent) -or
    (Split-Path -Leaf $Target) -ne $PluginName) {
    throw "Refusing unexpected marketplace target: $Target"
}
if (-not (Test-Path -LiteralPath $MarketplaceFile -PathType Leaf)) {
    throw "Personal marketplace not found: $MarketplaceFile"
}

$Catalog = Get-Content -LiteralPath $MarketplaceFile -Raw | ConvertFrom-Json
$Entries = @($Catalog.plugins | Where-Object { $_.name -eq $PluginName })
if ($Entries.Count -ne 1) {
    throw "Expected exactly one '$PluginName' entry in $MarketplaceFile"
}
$Entry = $Entries[0]
if ($Entry.source.source -ne "local" -or
    $Entry.source.path -ne $ExpectedSourcePath) {
    throw "The personal marketplace entry points to an unexpected source."
}

$ManifestPath = Join-Path $Source ".codex-plugin\plugin.json"
$Manifest = Get-Content -LiteralPath $ManifestPath -Raw | ConvertFrom-Json
if ($Manifest.name -ne $PluginName) {
    throw "Refusing package with unexpected plugin name: $($Manifest.name)"
}

$Uv = (Get-Command uv -CommandType Application -ErrorAction Stop).Source
$PreviousUvCache = $env:UV_CACHE_DIR
$UsingRepositoryUvCache = [string]::IsNullOrWhiteSpace($PreviousUvCache)
if ($UsingRepositoryUvCache) {
    $env:UV_CACHE_DIR = $RepositoryUvCache
}
Push-Location $RepositoryRoot
try {
    Write-Host "Validating source package before any marketplace change..."
    Invoke-Checked $Uv @("run", "python", $ValidatorProgram, $Source)

    $Action = "stage and replace version $($Manifest.version)"
    if (-not $PSCmdlet.ShouldProcess($Target, $Action)) {
        Write-Host "No marketplace files were changed."
        return
    }

    New-Item -ItemType Directory -Path $TargetParent -Force | Out-Null
    $Nonce = [Guid]::NewGuid().ToString("N")
    $StagingRoot = Join-Path $TargetParent ".$PluginName.staging.$Nonce"
    $Staging = Join-Path $StagingRoot $PluginName
    $Backup = Join-Path $TargetParent ".$PluginName.backup.$Nonce"
    Assert-ManagedTemporaryPath $StagingRoot
    Assert-ManagedTemporaryPath $Backup

    $OldPackageMoved = $false
    try {
        New-Item -ItemType Directory -Path $StagingRoot | Out-Null
        Copy-Item -LiteralPath $Source -Destination $Staging -Recurse
        Write-Host "Validating the staged marketplace package..."
        Invoke-Checked $Uv @("run", "python", $ValidatorProgram, $Staging)

        if (Test-Path -LiteralPath $Target) {
            Move-Item -LiteralPath $Target -Destination $Backup
            $OldPackageMoved = $true
        }
        Move-Item -LiteralPath $Staging -Destination $Target

        if ($OldPackageMoved -and (Test-Path -LiteralPath $Backup)) {
            try {
                Assert-ManagedTemporaryPath $Backup
                Remove-Item -LiteralPath $Backup -Recurse -Force
            }
            catch {
                Write-Warning "The update succeeded, but the backup remains at: $Backup"
            }
        }
    }
    catch {
        $Failure = $_
        if ($OldPackageMoved -and (Test-Path -LiteralPath $Backup)) {
            if (Test-Path -LiteralPath $Target) {
                Remove-Item -LiteralPath $Target -Recurse -Force
            }
            Move-Item -LiteralPath $Backup -Destination $Target
        }
        throw $Failure
    }
    finally {
        if (Test-Path -LiteralPath $StagingRoot) {
            Assert-ManagedTemporaryPath $StagingRoot
            Remove-Item -LiteralPath $StagingRoot -Recurse -Force
        }
    }

    Write-Host ""
    Write-Host "Personal marketplace package is ready."
    Write-Host "Version: $($Manifest.version)"
    Write-Host "Target: $Target"
    Write-Host ""
    Write-Host "Finish in Codex Desktop:"
    Write-Host "1. Open Plugins, then Personal, then AI Software Architect."
    Write-Host "2. Select Install or Update."
    Write-Host "3. Review and activate the current hook definitions."
    Write-Host "4. Start a new task and confirm the displayed version."
}
finally {
    Pop-Location
    if ($UsingRepositoryUvCache) {
        $env:UV_CACHE_DIR = $null
    }
}

# SPDX-FileCopyrightText: 2026 Leonardo Muffato (AUTOSOFT Engineering - www.autosoft-engineering.de)
# SPDX-License-Identifier: MIT

#Requires -Version 5.1

<#
.SYNOPSIS
Builds and validates the Codex plugin package.

.DESCRIPTION
Creates a cache-busted development version when PluginVersion is omitted. A full
build creates a new self-contained runtime. ReuseRuntime is intended only for
changes that cannot affect the reviewed runtime.

.PARAMETER PluginVersion
Semantic Versioning value written into the plugin manifest and provenance.

.PARAMETER ReuseRuntime
Reuses build/runtime/ai-architect-runtime instead of rebuilding the runtime.

.PARAMETER SkipSync
Skips uv sync. Intended for the release-gate wrapper after it has already synced.
#>

[CmdletBinding()]
param(
    [string]$PluginVersion,
    [switch]$ReuseRuntime,
    [switch]$SkipSync
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$RepositoryRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot ".."))
$BuildProgram = Join-Path $RepositoryRoot "adapters\codex\build_plugin.py"
$ValidatorProgram = Join-Path $RepositoryRoot "adapters\codex\validate_plugin.py"
$SmokeProgram = Join-Path $RepositoryRoot "adapters\codex\smoke_test_runtime.py"
$RuntimeDirectory = Join-Path $RepositoryRoot "build\runtime\ai-architect-runtime"
$PackageDirectory = Join-Path $RepositoryRoot "dist\codex\ai-software-architect"
$RuntimeExecutable = Join-Path $PackageDirectory `
    "runtime\windows-x86_64\ai-architect-runtime\ai-architect-runtime.exe"
$RepositoryUvCache = Join-Path $RepositoryRoot ".uv-cache"
$SemVerPattern = "^(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)(?:-[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*)?(?:\+[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*)?$"

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

if (-not (Test-Path -LiteralPath $BuildProgram -PathType Leaf)) {
    throw "Run this script from a complete AI Software Architect repository checkout."
}

$Uv = (Get-Command uv -CommandType Application -ErrorAction Stop).Source
$PreviousUvCache = $env:UV_CACHE_DIR
$UsingRepositoryUvCache = [string]::IsNullOrWhiteSpace($PreviousUvCache)
if ($UsingRepositoryUvCache) {
    $env:UV_CACHE_DIR = $RepositoryUvCache
}

if ([string]::IsNullOrWhiteSpace($PluginVersion)) {
    $Timestamp = (Get-Date).ToUniversalTime().ToString("yyyyMMddHHmmss")
    $PluginVersion = "0.1.0+codex.$Timestamp"
}
if ($PluginVersion -notmatch $SemVerPattern) {
    throw "PluginVersion is not valid Semantic Versioning: $PluginVersion"
}

Push-Location $RepositoryRoot
try {
    if (-not $SkipSync) {
        Write-Host "Synchronizing the locked development environment..."
        Invoke-Checked $Uv @("sync", "--locked", "--all-packages")
    }

    $BuildArguments = @(
        "run",
        "python",
        $BuildProgram
    )
    if ($ReuseRuntime) {
        if (-not (Test-Path -LiteralPath $RuntimeDirectory -PathType Container)) {
            throw "Reviewed runtime not found: $RuntimeDirectory"
        }
        Write-Host "Reusing the existing reviewed runtime..."
        $BuildArguments += @("--runtime", $RuntimeDirectory)
    }
    else {
        Write-Host "Building a new self-contained Windows x86-64 runtime..."
        $BuildArguments += "--build-runtime"
    }
    $BuildArguments += @("--plugin-version", $PluginVersion)

    Invoke-Checked $Uv $BuildArguments

    Write-Host "Validating the assembled plugin and its provenance..."
    Invoke-Checked $Uv @(
        "run",
        "python",
        $ValidatorProgram,
        $PackageDirectory
    )

    Write-Host "Smoke-testing the packaged short-lived hook runtime..."
    Invoke-Checked $Uv @(
        "run",
        "python",
        $SmokeProgram,
        $RuntimeExecutable
    )

    $ManifestPath = Join-Path $PackageDirectory ".codex-plugin\plugin.json"
    $Manifest = Get-Content -LiteralPath $ManifestPath -Raw | ConvertFrom-Json
    if ($Manifest.version -ne $PluginVersion) {
        throw "Built manifest version '$($Manifest.version)' does not match '$PluginVersion'."
    }

    Write-Host ""
    Write-Host "Codex plugin package is ready."
    Write-Host "Version: $PluginVersion"
    Write-Host "Package: $PackageDirectory"
}
finally {
    Pop-Location
    if ($UsingRepositoryUvCache) {
        $env:UV_CACHE_DIR = $null
    }
}

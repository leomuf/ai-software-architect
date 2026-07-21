# SPDX-FileCopyrightText: 2026 Leonardo Muffato (AUTOSOFT Engineering - www.autosoft-engineering.de)
# SPDX-License-Identifier: MIT

#Requires -Version 5.1

<#
.SYNOPSIS
Runs deterministic release-candidate gates and builds the exact Codex release.

.DESCRIPTION
Requires a clean candidate commit. Runs the locked-environment, generated-file,
lint, type-check, test, full-build, package-validation, and runtime-smoke gates.
It then creates the dependency-free marketplace bundle and checksum.
Manual package inspection, exploratory Codex tests, Desktop lifecycle acceptance,
and clean-machine acceptance remain separate documented release gates.

.PARAMETER PluginVersion
Public Semantic Versioning value, without the Git tag's leading v.
#>

[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$PluginVersion
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$RepositoryRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot ".."))
$BuildScript = Join-Path $PSScriptRoot "build-codex-plugin.ps1"
$ReleasePackageScript = Join-Path $PSScriptRoot "package-codex-release.ps1"
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

function Assert-CleanWorkingTree {
    param(
        [Parameter(Mandatory = $true)]
        [string]$GitCommand,

        [Parameter(Mandatory = $true)]
        [string]$Stage
    )

    $Status = @(& $GitCommand status --porcelain=v1 --untracked-files=all)
    if ($LASTEXITCODE -ne 0) {
        throw "Unable to inspect the Git working tree during $Stage."
    }
    if ($Status.Count -ne 0) {
        throw "Release candidate working tree is not clean during ${Stage}:`n$($Status -join "`n")"
    }
}

if ($PluginVersion -notmatch $SemVerPattern) {
    throw "PluginVersion is not valid Semantic Versioning: $PluginVersion"
}
if (-not (Test-Path -LiteralPath $BuildScript -PathType Leaf)) {
    throw "Build wrapper not found: $BuildScript"
}
if (-not (Test-Path -LiteralPath $ReleasePackageScript -PathType Leaf)) {
    throw "Release packaging wrapper not found: $ReleasePackageScript"
}

$Uv = (Get-Command uv -CommandType Application -ErrorAction Stop).Source
$Git = (Get-Command git -CommandType Application -ErrorAction Stop).Source
$PreviousUvCache = $env:UV_CACHE_DIR
$UsingRepositoryUvCache = [string]::IsNullOrWhiteSpace($PreviousUvCache)
if ($UsingRepositoryUvCache) {
    $env:UV_CACHE_DIR = $RepositoryUvCache
}

Push-Location $RepositoryRoot
try {
    Assert-CleanWorkingTree $Git "candidate start"

    Write-Host "Checking and synchronizing the locked environment..."
    Invoke-Checked $Uv @("lock", "--check")
    Invoke-Checked $Uv @("sync", "--locked", "--all-packages")

    Write-Host "Regenerating deterministic repository artifacts..."
    Invoke-Checked $Uv @("run", "python", "shared/schemas/generate_schema.py")
    Invoke-Checked $Uv @("run", "python", "shared/evaluations/generate_acceptance.py")
    Invoke-Checked $Uv @("run", "python", "tools/generate_third_party_notices.py")
    Assert-CleanWorkingTree $Git "generated-artifact verification"

    Write-Host "Running lint, type, and test gates..."
    Invoke-Checked $Uv @(
        "run",
        "ruff",
        "check",
        "shared/schemas",
        "tools/python-mcp",
        "adapters",
        "tests"
    )
    Invoke-Checked $Uv @("run", "mypy")
    Invoke-Checked $Uv @("run", "pytest", "-q")

    Write-Host "Building and validating the exact release candidate..."
    & $BuildScript -PluginVersion $PluginVersion -SkipSync

    Write-Host "Creating the dependency-free marketplace bundle..."
    & $ReleasePackageScript -PluginVersion $PluginVersion

    Assert-CleanWorkingTree $Git "candidate completion"

    Write-Host ""
    Write-Host "Deterministic release-candidate gates passed for $PluginVersion."
    Write-Host "Continue with manual Gates B-E in docs/RELEASING.md."
}
finally {
    Pop-Location
    if ($UsingRepositoryUvCache) {
        $env:UV_CACHE_DIR = $null
    }
}

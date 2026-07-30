# SPDX-FileCopyrightText: 2026 Leonardo Muffato (AUTOSOFT Engineering - www.autosoft-engineering.de)
# SPDX-License-Identifier: MIT

<#
.SYNOPSIS
Previews or applies existing exploratory report.json files to performance history.

.DESCRIPTION
Preview is the default. Use -Apply only after reviewing the generated JSON file.
#>

[CmdletBinding()]
param(
    [string[]]$Report,
    [string]$ReportsRoot,
    [string]$Preview,
    [ValidateSet("standard", "fast", "unknown")]
    [string]$Speed = "unknown",
    [string]$GitCommit = "unknown",
    [string]$HostName,
    [switch]$Apply
)

$ErrorActionPreference = "Stop"
$repositoryRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
if (-not $ReportsRoot -and -not $Report) {
    $ReportsRoot = Join-Path $repositoryRoot ".tmp\evaluations"
}
if (-not $Preview) {
    $stamp = [DateTime]::UtcNow.ToString("yyyyMMddTHHmmssZ")
    $Preview = Join-Path $repositoryRoot ".tmp\evaluations\imports\$stamp.json"
}

$arguments = @(
    "run", "python", "-m", "adapters.codex.evaluations.performance_import",
    "--preview", $Preview,
    "--speed", $Speed,
    "--git-commit", $GitCommit
)
$uvArguments = @()
if (-not $env:UV_CACHE_DIR) {
    $uvArguments += @("--cache-dir", (Join-Path $repositoryRoot ".uv-cache"))
}
if ($ReportsRoot) {
    $arguments += @("--reports-root", $ReportsRoot)
}
foreach ($reportPath in $Report) {
    $arguments += @("--report", $reportPath)
}
if ($HostName) {
    $arguments += @("--host", $HostName)
}
if ($Apply) {
    $arguments += "--apply"
}

& uv @uvArguments @arguments
if ($LASTEXITCODE -ne 0) {
    throw "Exploratory performance report import failed with exit code $LASTEXITCODE."
}

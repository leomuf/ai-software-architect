# SPDX-FileCopyrightText: 2026 Leonardo Muffato (AUTOSOFT Engineering - www.autosoft-engineering.de)
# SPDX-License-Identifier: MIT

<#
.SYNOPSIS
Renders the canonical exploratory performance history as Markdown, CSV, and JSON.
#>

[CmdletBinding()]
param(
    [string]$Ledger,
    [string]$OutputDirectory
)

$ErrorActionPreference = "Stop"
$repositoryRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
if (-not $OutputDirectory) {
    $stamp = [DateTime]::UtcNow.ToString("yyyyMMddTHHmmssZ")
    $OutputDirectory = Join-Path $repositoryRoot ".tmp\evaluations\performance\$stamp"
}

$arguments = @(
    "run", "python", "-m", "adapters.codex.evaluations.performance_report",
    "--output-directory", $OutputDirectory
)
$uvArguments = @()
if (-not $env:UV_CACHE_DIR) {
    $uvArguments += @("--cache-dir", (Join-Path $repositoryRoot ".uv-cache"))
}
if ($Ledger) {
    $arguments += @("--ledger", $Ledger)
}

& uv @uvArguments @arguments
if ($LASTEXITCODE -ne 0) {
    throw "Exploratory performance reporting failed with exit code $LASTEXITCODE."
}

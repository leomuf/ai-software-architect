# SPDX-FileCopyrightText: 2026 Leonardo Muffato (AUTOSOFT Engineering - www.autosoft-engineering.de)
# SPDX-License-Identifier: MIT

<#
.SYNOPSIS
Applies an approved Codex-assisted historical review to the canonical ledger.
#>

[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$Review,
    [string]$Ledger
)

$ErrorActionPreference = "Stop"
$repositoryRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$arguments = @(
    "run", "python", "-m", "adapters.codex.evaluations.historical_review",
    "apply",
    "--review", $Review
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
    throw "Codex exploratory history review failed with exit code $LASTEXITCODE."
}

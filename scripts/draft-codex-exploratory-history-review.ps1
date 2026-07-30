# SPDX-FileCopyrightText: 2026 Leonardo Muffato (AUTOSOFT Engineering - www.autosoft-engineering.de)
# SPDX-License-Identifier: MIT

<#
.SYNOPSIS
Creates a schema-validated review draft from exported Codex exploratory tasks.

.DESCRIPTION
Completed timestamped phases remain needs-review. This script never approves
semantic eligibility; Codex or a human reviewer must inspect the bounded evidence.
#>

[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$Export,
    [Parameter(Mandatory = $true)]
    [string]$ReviewerSessionId,
    [string]$Output
)

$ErrorActionPreference = "Stop"
$repositoryRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
if (-not $Output) {
    $stamp = [DateTime]::UtcNow.ToString("yyyyMMddTHHmmssZ")
    $Output = Join-Path $repositoryRoot ".tmp\evaluations\history\review-$stamp.json"
}

$arguments = @(
    "run", "python", "-m", "adapters.codex.evaluations.historical_review",
    "draft",
    "--export", $Export,
    "--output", $Output,
    "--reviewer-session-id", $ReviewerSessionId
)
$uvArguments = @()
if (-not $env:UV_CACHE_DIR) {
    $uvArguments += @("--cache-dir", (Join-Path $repositoryRoot ".uv-cache"))
}

& uv @uvArguments @arguments
if ($LASTEXITCODE -ne 0) {
    throw "Codex exploratory history review drafting failed with exit code $LASTEXITCODE."
}

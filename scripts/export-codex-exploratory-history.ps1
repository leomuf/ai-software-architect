# SPDX-FileCopyrightText: 2026 Leonardo Muffato (AUTOSOFT Engineering - www.autosoft-engineering.de)
# SPDX-License-Identifier: MIT

<#
.SYNOPSIS
Exports archived Codex exploratory tasks for a bounded Codex-assisted review.
#>

[CmdletBinding()]
param(
    [string]$CodexCommand,
    [string]$Output,
    [string[]]$TaskId,
    [switch]$Active
)

$ErrorActionPreference = "Stop"
$repositoryRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
if (-not $CodexCommand) {
    $bundledRoot = Join-Path $env:LOCALAPPDATA "OpenAI\Codex\bin"
    $bundled = Get-ChildItem -LiteralPath $bundledRoot -Filter codex.exe -Recurse `
        -ErrorAction SilentlyContinue |
        Sort-Object LastWriteTimeUtc -Descending |
        Select-Object -First 1
    if (-not $bundled) {
        throw "Codex CLI was not found. Pass -CodexCommand with the full path."
    }
    $CodexCommand = $bundled.FullName
}
if (-not $Output) {
    $stamp = [DateTime]::UtcNow.ToString("yyyyMMddTHHmmssZ")
    $Output = Join-Path $repositoryRoot ".tmp\evaluations\history\$stamp.json"
}

$arguments = @(
    "run", "python", "-m", "adapters.codex.evaluations.historical_review",
    "export",
    "--codex-command", $CodexCommand,
    "--output", $Output
)
$uvArguments = @()
if (-not $env:UV_CACHE_DIR) {
    $uvArguments += @("--cache-dir", (Join-Path $repositoryRoot ".uv-cache"))
}
foreach ($id in $TaskId) {
    $arguments += @("--task-id", $id)
}
if ($Active) {
    $arguments += "--active"
}

& uv @uvArguments @arguments
if ($LASTEXITCODE -ne 0) {
    throw "Codex exploratory history export failed with exit code $LASTEXITCODE."
}

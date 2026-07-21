# SPDX-FileCopyrightText: 2026 Leonardo Muffato (AUTOSOFT Engineering - www.autosoft-engineering.de)
# SPDX-License-Identifier: MIT

<#
.SYNOPSIS
Runs the shared exploratory campaign through the Codex-specific Python runner.

.DESCRIPTION
This is a thin developer-facing entry point. It resolves Codex, selects an output
directory below .tmp/evaluations, and delegates all fixture and grading logic to
adapters/codex/evaluations.
#>

[CmdletBinding()]
param(
    [string[]]$Fixture,
    [string]$Model = "gpt-5.6",
    [string]$PluginVersion,
    [ValidateSet("low", "medium", "high", "xhigh")]
    [string]$ReasoningEffort = "medium",
    [ValidateRange(1, 7200)]
    [int]$TimeoutSeconds = 600,
    [string]$OutputDirectory,
    [string]$CodexCommand,
    [switch]$ContinueOnFailure,
    [switch]$DryRun
)

$ErrorActionPreference = "Stop"
$repositoryRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path

if (-not $OutputDirectory) {
    $stamp = [DateTime]::UtcNow.ToString("yyyyMMddTHHmmssZ")
    $OutputDirectory = Join-Path $repositoryRoot ".tmp\evaluations\$stamp"
}

if (-not $DryRun -and -not $CodexCommand) {
    $bundledRoot = Join-Path $env:LOCALAPPDATA "OpenAI\Codex\bin"
    $bundled = Get-ChildItem -LiteralPath $bundledRoot -Filter codex.exe -Recurse `
        -ErrorAction SilentlyContinue |
        Sort-Object LastWriteTimeUtc -Descending |
        Select-Object -First 1
    if ($bundled) {
        $CodexCommand = $bundled.FullName
    }
    else {
        $resolved = Get-Command codex -ErrorAction SilentlyContinue
        if ($resolved) {
            $CodexCommand = $resolved.Source
        }
        else {
            throw "Codex CLI was not found. Pass -CodexCommand with the full path to codex.exe."
        }
    }
}
if (-not $CodexCommand) {
    $CodexCommand = "codex"
}

$arguments = @(
    "run", "python", "-m", "adapters.codex.evaluations.runner",
    "--output-directory", $OutputDirectory,
    "--codex-command", $CodexCommand,
    "--model", $Model,
    "--reasoning-effort", $ReasoningEffort,
    "--timeout-seconds", $TimeoutSeconds.ToString()
)
if ($PluginVersion) {
    $arguments += @("--plugin-version", $PluginVersion)
}
foreach ($fixtureId in $Fixture) {
    $arguments += @("--fixture", $fixtureId)
}
if ($ContinueOnFailure) {
    $arguments += "--continue-on-failure"
}
if ($DryRun) {
    $arguments += "--dry-run"
}

Push-Location $repositoryRoot
try {
    & uv @arguments
    if ($LASTEXITCODE -ne 0) {
        throw "Codex exploratory evaluations failed with exit code $LASTEXITCODE."
    }
}
finally {
    Pop-Location
}

Write-Host "Evaluation evidence: $OutputDirectory"

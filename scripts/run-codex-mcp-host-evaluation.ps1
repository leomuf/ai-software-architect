# SPDX-FileCopyrightText: 2026 Leonardo Muffato (AUTOSOFT Engineering - www.autosoft-engineering.de)
# SPDX-License-Identifier: MIT

[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][string]$Model,
    [ValidateSet('low', 'medium', 'high', 'xhigh')][string]$ReasoningEffort = 'medium',
    [ValidateSet('standard', 'fast')][string]$Speed = 'standard',
    [ValidateRange(1, 7200)][int]$TimeoutSeconds = 600,
    [ValidateRange(1, 500)][int]$MaxToolCalls = 50,
    [ValidateSet('local-review-export', 'context-loss', 'two-active-reviews')]
    [string]$Scenario = 'local-review-export',
    [string]$OutputDirectory,
    [string]$CodexCommand = 'codex'
)

$ErrorActionPreference = 'Stop'
$repositoryRoot = Split-Path -Parent $PSScriptRoot
if (-not $OutputDirectory) {
    $OutputDirectory = Join-Path $repositoryRoot ('.tmp/mcp-host/' + [DateTime]::UtcNow.ToString('yyyyMMddTHHmmssZ'))
}
$previousUvCache = $env:UV_CACHE_DIR
Push-Location -LiteralPath $repositoryRoot
try {
    $env:UV_CACHE_DIR = Join-Path $repositoryRoot '.uv-cache'
    & uv run --locked python -m adapters.mcp.codex_host_evaluation --output $OutputDirectory `
        --model $Model --reasoning-effort $ReasoningEffort --speed $Speed `
        --timeout-seconds $TimeoutSeconds --max-tool-calls $MaxToolCalls --codex-command $CodexCommand `
        --scenario $Scenario
    if ($LASTEXITCODE -ne 0) {
        throw "Codex MCP host diagnostic failed; inspect $OutputDirectory/report.json and evidence."
    }
}
finally {
    $env:UV_CACHE_DIR = $previousUvCache
    Pop-Location
}

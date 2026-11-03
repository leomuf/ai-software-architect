# SPDX-FileCopyrightText: 2026 Leonardo Muffato (AUTOSOFT Engineering - www.autosoft-engineering.de)
# SPDX-License-Identifier: MIT

[CmdletBinding()]
param(
    [string]$OutputDirectory
)

$ErrorActionPreference = 'Stop'
$repositoryRoot = Split-Path -Parent $PSScriptRoot
if (-not $OutputDirectory) {
    $OutputDirectory = Join-Path $repositoryRoot ('.tmp/mcp-prototype/' + (Get-Date -Format 'yyyyMMdd-HHmmss'))
}
$previousUvCache = $env:UV_CACHE_DIR
Push-Location -LiteralPath $repositoryRoot
try {
    $env:UV_CACHE_DIR = Join-Path $repositoryRoot '.uv-cache'
    & uv run --locked python -m adapters.mcp.prototype_evaluation --output $OutputDirectory
    if ($LASTEXITCODE -ne 0) {
        throw "MCP prototype deterministic evaluation failed (exit $LASTEXITCODE)."
    }
}
finally {
    $env:UV_CACHE_DIR = $previousUvCache
    Pop-Location
}

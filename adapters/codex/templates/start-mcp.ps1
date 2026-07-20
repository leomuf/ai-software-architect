# SPDX-FileCopyrightText: 2026 Leonardo Muffato (AUTOSOFT Engineering - www.autosoft-engineering.de)
# SPDX-License-Identifier: MIT

#Requires -Version 5.1

[CmdletBinding()]
param()

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$PluginRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot ".."))
$LocalAppData = $env:LOCALAPPDATA
if ([string]::IsNullOrWhiteSpace($LocalAppData)) {
    throw "LOCALAPPDATA is unavailable."
}
$LocalAppData = [IO.Path]::GetFullPath($LocalAppData)

$ManifestPath = Join-Path $PluginRoot ".codex-plugin\plugin.json"
$Manifest = Get-Content -LiteralPath $ManifestPath -Raw | ConvertFrom-Json
$Version = [string]$Manifest.version
if ($Version -notmatch '^[0-9A-Za-z.+-]+$') {
    throw "The packaged plugin version is invalid."
}

$Source = Join-Path $PluginRoot "runtime\windows-x86_64\ai-architect-mcp"
$RuntimeParent = Join-Path $LocalAppData "AI Software Architect\plugin-runtime\$Version"
$Runtime = Join-Path $RuntimeParent ([Guid]::NewGuid().ToString("N"))
$Executable = Join-Path $Runtime "ai-architect-mcp.exe"

if (-not (Test-Path -LiteralPath $Source -PathType Container)) {
    throw "The packaged MCP runtime is unavailable."
}

New-Item -ItemType Directory -Force -Path $RuntimeParent | Out-Null
$ProcessExitCode = 1
try {
    Copy-Item -LiteralPath $Source -Destination $Runtime -Recurse
    if (-not (Test-Path -LiteralPath $Executable -PathType Leaf)) {
        throw "The private MCP runtime copy is unavailable."
    }

    # A process whose current directory is inside the versioned plugin cache can
    # keep that cache locked on Windows. Leave it before starting the long-lived
    # MCP process; the copied executable then owns no cache path.
    Set-Location -LiteralPath $LocalAppData
    & $Executable
    $ProcessExitCode = $LASTEXITCODE
}
finally {
    Set-Location -LiteralPath $LocalAppData
    if (Test-Path -LiteralPath $Runtime) {
        Remove-Item -LiteralPath $Runtime -Recurse -Force
    }
}

exit $ProcessExitCode

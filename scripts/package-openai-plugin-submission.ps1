# SPDX-FileCopyrightText: 2026 Leonardo Muffato (AUTOSOFT Engineering - www.autosoft-engineering.de)
# SPDX-License-Identifier: MIT

#Requires -Version 5.1

<#
.SYNOPSIS
Creates the dedicated OpenAI plugin-directory submission archive.

.DESCRIPTION
Validates an already assembled AI Software Architect plugin, archives the plugin
root without a marketplace wrapper, verifies the resulting ZIP layout, and writes
a SHA-256 checksum. The script does not build, install, submit, or publish the
plugin.

.PARAMETER PluginPath
Path to the assembled plugin. Relative paths resolve from the repository root.

.PARAMETER OutputDirectory
Directory for the ZIP and checksum. Relative paths resolve from the repository root.

.PARAMETER PluginVersion
Expected Semantic Versioning value. When omitted, the manifest version is used.

.EXAMPLE
.\scripts\package-openai-plugin-submission.ps1 -PluginVersion 0.2.1
#>

[CmdletBinding()]
param(
    [string]$PluginPath = "dist\codex\ai-software-architect",
    [string]$OutputDirectory = "dist\openai-submission",
    [string]$PluginVersion
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$PluginName = "ai-software-architect"
$RepositoryRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot ".."))
$SemVerPattern = "^(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)(?:-[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*)?(?:\+[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*)?$"

function Resolve-RepositoryPath {
    param([Parameter(Mandatory = $true)][string]$Path)

    if ([IO.Path]::IsPathRooted($Path)) {
        return [IO.Path]::GetFullPath($Path)
    }
    return [IO.Path]::GetFullPath((Join-Path $RepositoryRoot $Path))
}

$Source = Resolve-RepositoryPath $PluginPath
$OutputRoot = Resolve-RepositoryPath $OutputDirectory
if (-not (Test-Path -LiteralPath $Source -PathType Container)) {
    throw "Assembled plugin not found: $Source"
}

$ManifestPath = Join-Path $Source ".codex-plugin\plugin.json"
if (-not (Test-Path -LiteralPath $ManifestPath -PathType Leaf)) {
    throw "Plugin manifest not found: $ManifestPath"
}
$Manifest = Get-Content -LiteralPath $ManifestPath -Raw | ConvertFrom-Json
if ($Manifest.name -ne $PluginName) {
    throw "Unexpected plugin name in manifest: $($Manifest.name)"
}
if ([string]::IsNullOrWhiteSpace($PluginVersion)) {
    $PluginVersion = [string]$Manifest.version
}
if ($PluginVersion -notmatch $SemVerPattern) {
    throw "PluginVersion is not valid Semantic Versioning: $PluginVersion"
}
if ($Manifest.version -ne $PluginVersion) {
    throw "Built manifest version '$($Manifest.version)' does not match '$PluginVersion'."
}

$Uv = Get-Command uv -CommandType Application -ErrorAction Stop |
    Select-Object -First 1 -ExpandProperty Source
& $Uv run python adapters/codex/validate_plugin.py $Source
if ($LASTEXITCODE -ne 0) {
    throw "Plugin validation failed with exit code $LASTEXITCODE."
}

$ArchiveName = "$PluginName-v$PluginVersion-openai-plugin.zip"
$ArchivePath = Join-Path $OutputRoot $ArchiveName
$ChecksumPath = Join-Path $OutputRoot "SHA256SUMS-openai-plugin.txt"
foreach ($Path in @($ArchivePath, $ChecksumPath)) {
    $FullPath = [IO.Path]::GetFullPath($Path)
    if (-not [StringComparer]::OrdinalIgnoreCase.Equals(
        [IO.Path]::GetFullPath((Split-Path -Parent $FullPath)),
        $OutputRoot
    )) {
        throw "Refusing unexpected submission target: $FullPath"
    }
}

New-Item -ItemType Directory -Path $OutputRoot -Force | Out-Null
foreach ($OldPath in @($ArchivePath, $ChecksumPath)) {
    if (Test-Path -LiteralPath $OldPath) {
        Remove-Item -LiteralPath $OldPath -Force
    }
}

# Compress-Archive can omit dot-prefixed paths. tar.exe preserves the required
# .codex-plugin directory while placing the plugin contents at the ZIP root.
$Tar = Get-Command tar.exe -CommandType Application -ErrorAction Stop |
    Select-Object -First 1 -ExpandProperty Source
& $Tar -a -c -f $ArchivePath -C $Source .
if ($LASTEXITCODE -ne 0) {
    throw "tar.exe failed to create '$ArchivePath' with exit code $LASTEXITCODE."
}

Add-Type -AssemblyName System.IO.Compression.FileSystem
$Archive = [IO.Compression.ZipFile]::OpenRead($ArchivePath)
try {
    $Members = @(
        $Archive.Entries |
            ForEach-Object {
                $Normalized = $_.FullName.Replace("\", "/")
                if ($Normalized.StartsWith("./", [StringComparison]::Ordinal)) {
                    $Normalized.Substring(2)
                } else {
                    $Normalized
                }
            }
    )
    foreach ($RequiredMember in @(
        ".codex-plugin/plugin.json",
        "skills/ai-software-architect/SKILL.md",
        "hooks/hooks.json",
        "provenance.json",
        "PRIVACY.md",
        "TERMS.md",
        "SUPPORT.md"
    )) {
        if ($Members -notcontains $RequiredMember) {
            throw "Submission archive is missing required root member: $RequiredMember"
        }
    }
    if ($Members -contains ".agents/plugins/marketplace.json") {
        throw "Submission archive must not contain the local marketplace wrapper."
    }
} finally {
    $Archive.Dispose()
}

$ArchiveHash = (Get-FileHash -LiteralPath $ArchivePath -Algorithm SHA256).Hash.ToLowerInvariant()
Set-Content -LiteralPath $ChecksumPath -Value "$ArchiveHash  $ArchiveName`n" -Encoding ascii

Write-Host ""
Write-Host "OpenAI plugin submission archive is ready."
Write-Host "Brand: AUTOSOFT Engineering"
Write-Host "Legal publisher: XAVIER MUFFATO LTDA"
Write-Host "Version: $PluginVersion"
Write-Host "Archive: $ArchivePath"
Write-Host "Checksum: $ChecksumPath"
Write-Host "This script did not upload or publish the plugin."

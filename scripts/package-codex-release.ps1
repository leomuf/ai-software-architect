# SPDX-FileCopyrightText: 2026 Leonardo Muffato (AUTOSOFT Engineering - www.autosoft-engineering.de)
# SPDX-License-Identifier: MIT

#Requires -Version 5.1

<#
.SYNOPSIS
Creates a dependency-free, installable Codex marketplace bundle.

.DESCRIPTION
Packages an already built and validated AI Software Architect plugin together
with a repository marketplace catalog and installation guide. This script does
not build or validate the plugin runtime; run the release-candidate gates first.

.PARAMETER PluginPath
Path to the assembled plugin. Relative paths resolve from the repository root.

.PARAMETER OutputDirectory
Directory for the expanded bundle, ZIP, and SHA256SUMS.txt. Relative paths
resolve from the repository root.

.PARAMETER PluginVersion
Expected Semantic Versioning value. When omitted, the script uses the version
from the plugin manifest.

.EXAMPLE
.\scripts\package-codex-release.ps1 -PluginVersion 0.1.0
#>

[CmdletBinding()]
param(
    [string]$PluginPath = "dist\codex\ai-software-architect",
    [string]$OutputDirectory = "dist\release",
    [string]$PluginVersion
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$PluginName = "ai-software-architect"
$RepositoryRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot ".."))
$MarketplaceTemplate = Join-Path $RepositoryRoot "adapters\codex\templates\marketplace.json"
$InstallGuide = Join-Path $RepositoryRoot "docs\INSTALL_CODEX_PLUGIN.md"
$SemVerPattern = "^(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)(?:-[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*)?(?:\+[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*)?$"

function Resolve-RepositoryPath {
    param([Parameter(Mandatory = $true)][string]$Path)

    if ([IO.Path]::IsPathRooted($Path)) {
        return [IO.Path]::GetFullPath($Path)
    }
    return [IO.Path]::GetFullPath((Join-Path $RepositoryRoot $Path))
}

function Assert-SafeBundleTarget {
    param(
        [Parameter(Mandatory = $true)][string]$Path,
        [Parameter(Mandatory = $true)][string]$ExpectedParent,
        [Parameter(Mandatory = $true)][string]$ExpectedLeaf
    )

    $FullPath = [IO.Path]::GetFullPath($Path)
    $Parent = [IO.Path]::GetFullPath((Split-Path -Parent $FullPath))
    if (-not [StringComparer]::OrdinalIgnoreCase.Equals($Parent, $ExpectedParent) -or
        (Split-Path -Leaf $FullPath) -ne $ExpectedLeaf) {
        throw "Refusing unexpected release target: $FullPath"
    }
}

$Source = Resolve-RepositoryPath $PluginPath
$ReleaseRoot = Resolve-RepositoryPath $OutputDirectory
if (-not (Test-Path -LiteralPath $Source -PathType Container)) {
    throw "Assembled plugin not found: $Source"
}
foreach ($RequiredFile in @($MarketplaceTemplate, $InstallGuide)) {
    if (-not (Test-Path -LiteralPath $RequiredFile -PathType Leaf)) {
        throw "Required release source not found: $RequiredFile"
    }
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

$BundleName = "$PluginName-v$PluginVersion-windows-x86_64"
$BundleRoot = Join-Path $ReleaseRoot $BundleName
$ArchivePath = Join-Path $ReleaseRoot "$BundleName.zip"
$ChecksumPath = Join-Path $ReleaseRoot "SHA256SUMS.txt"
Assert-SafeBundleTarget $BundleRoot $ReleaseRoot $BundleName
Assert-SafeBundleTarget $ArchivePath $ReleaseRoot "$BundleName.zip"
Assert-SafeBundleTarget $ChecksumPath $ReleaseRoot "SHA256SUMS.txt"

New-Item -ItemType Directory -Path $ReleaseRoot -Force | Out-Null
foreach ($OldPath in @($BundleRoot, $ArchivePath, $ChecksumPath)) {
    if (Test-Path -LiteralPath $OldPath) {
        Remove-Item -LiteralPath $OldPath -Recurse -Force
    }
}

$MarketplaceDirectory = Join-Path $BundleRoot ".agents\plugins"
$PluginTargetParent = Join-Path $BundleRoot "plugins"
$PluginTarget = Join-Path $PluginTargetParent $PluginName
New-Item -ItemType Directory -Path $MarketplaceDirectory -Force | Out-Null
New-Item -ItemType Directory -Path $PluginTargetParent -Force | Out-Null
Copy-Item -LiteralPath $MarketplaceTemplate `
    -Destination (Join-Path $MarketplaceDirectory "marketplace.json")
Copy-Item -LiteralPath $Source -Destination $PluginTarget -Recurse

$InstallText = Get-Content -LiteralPath $InstallGuide -Raw
$InstallText = $InstallText.Replace("v0.1.0", "v$PluginVersion")
Set-Content -LiteralPath (Join-Path $BundleRoot "INSTALL.md") `
    -Value $InstallText -Encoding utf8
Set-Content -LiteralPath (Join-Path $BundleRoot "VERSION.txt") `
    -Value "$PluginVersion`n" -Encoding ascii

$Tar = (Get-Command tar.exe -CommandType Application -ErrorAction Stop).Source
& $Tar -a -c -f $ArchivePath -C $ReleaseRoot $BundleName
if ($LASTEXITCODE -ne 0) {
    throw "tar.exe failed to create the release archive."
}

$ArchiveHash = (Get-FileHash -LiteralPath $ArchivePath -Algorithm SHA256).Hash.ToLowerInvariant()
Set-Content -LiteralPath $ChecksumPath `
    -Value "$ArchiveHash  $($BundleName).zip`n" -Encoding ascii

Write-Host ""
Write-Host "Installable Codex release bundle is ready."
Write-Host "Version: $PluginVersion"
Write-Host "Expanded bundle: $BundleRoot"
Write-Host "Archive: $ArchivePath"
Write-Host "Checksum: $ChecksumPath"

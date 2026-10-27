# SPDX-FileCopyrightText: 2026 Leonardo Muffato (AUTOSOFT Engineering - www.autosoft-engineering.de)
# SPDX-License-Identifier: MIT

#Requires -Version 5.1

<#
.SYNOPSIS
Lists unsigned runtime binaries for signing, or verifies a signed release runtime.
.DESCRIPTION
Run before plugin assembly and provenance generation. Existing valid embedded
signatures are preserved. Invalid signatures and linked paths stop the operation.
This script never signs files or changes Windows trust settings.
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$RuntimePath,
    [ValidateSet('ListUnsigned', 'Verify')]
    [string]$Mode = 'Verify',
    [string]$ExpectedPublisherSubject,
    [string]$SignToolPath
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
if ($env:OS -ne 'Windows_NT') { throw 'Windows signature verification requires Windows.' }
Import-Module (Join-Path $PSHOME 'Modules\Microsoft.PowerShell.Security\Microsoft.PowerShell.Security.psd1')
if ($Mode -eq 'Verify' -and [string]::IsNullOrWhiteSpace($ExpectedPublisherSubject)) {
    throw 'ExpectedPublisherSubject is required for release verification.'
}
$root = Get-Item -LiteralPath $RuntimePath -Force
if (-not $root.PSIsContainer) { throw 'RuntimePath must be a runtime directory.' }
$entries = @($root) + @(Get-ChildItem -LiteralPath $root.FullName -Recurse -Force)
if (@($entries | Where-Object { $_.Attributes -band [IO.FileAttributes]::ReparsePoint }).Count) {
    throw 'Linked or reparse-point paths are not allowed in a signing input.'
}
$mainPath = Join-Path $root.FullName 'ai-architect-runtime.exe'
if (-not (Test-Path -LiteralPath $mainPath -PathType Leaf)) {
    throw 'The runtime entry executable is missing.'
}
$binaryCount = 0
foreach ($file in ($entries | Where-Object { -not $_.PSIsContainer } | Sort-Object FullName)) {
    $stream = [IO.File]::OpenRead($file.FullName)
    try { $isPe = ($stream.ReadByte() -eq 77 -and $stream.ReadByte() -eq 90) }
    finally { $stream.Dispose() }
    if (-not $isPe) {
        if ($file.Extension -in @('.exe', '.dll', '.pyd')) {
            throw "Expected a Windows binary: $($file.FullName)"
        }
        continue
    }
    $binaryCount++
    $signature = Get-AuthenticodeSignature -LiteralPath $file.FullName
    # PowerShell prefers a host catalog if one exists. Such a catalog is not
    # shipped with the runtime, so those files need portable embedded signing.
    $catalogOnly = $signature.Status -eq 'Valid' -and $signature.SignatureType -eq 'Catalog'
    if (($signature.Status -eq 'NotSigned' -or $catalogOnly) -and $Mode -eq 'ListUnsigned') {
        $file.FullName
        continue
    }
    if ($signature.Status -ne 'Valid') {
        throw "Invalid or missing embedded signature ($($signature.Status)): $($file.FullName)"
    }
    if ($catalogOnly) {
        if ([string]::IsNullOrWhiteSpace($SignToolPath)) {
            $sdk = Join-Path ${env:ProgramFiles(x86)} 'Windows Kits\10\bin'
            $candidate = Get-ChildItem -Path (Join-Path $sdk '*\x64\signtool.exe') |
                Sort-Object FullName -Descending | Select-Object -First 1
            if ($null -ne $candidate) { $SignToolPath = $candidate.FullName }
        }
        if (-not [IO.Path]::IsPathRooted($SignToolPath) -or
            -not (Test-Path -LiteralPath $SignToolPath -PathType Leaf)) {
            throw 'The Windows SDK SignTool is required to check an embedded signature behind a catalog match.'
        }
        # Omitting /a prevents SignTool from falling back to catalog lookup.
        try { $null = & $SignToolPath verify /pa /all $file.FullName 2>&1 }
        catch { throw "Embedded signature verification failed: $($file.FullName)" }
        if ($LASTEXITCODE -ne 0) {
            throw "Embedded signature verification failed: $($file.FullName)"
        }
        if ($file.FullName -eq $mainPath) {
            throw 'The entry executable must expose its embedded publisher identity, not a catalog identity.'
        }
        continue
    }
    if ($signature.SignatureType -ne 'Authenticode') {
        throw "An embedded Authenticode signature is required: $($file.FullName)"
    }
    $eku = @($signature.SignerCertificate.Extensions | Where-Object {
        $_.Oid.Value -eq '2.5.29.37'
    } | ForEach-Object { $_.EnhancedKeyUsages } | ForEach-Object { $_.Value })
    if ($eku -notcontains '1.3.6.1.5.5.7.3.3') {
        throw "A Code Signing certificate is required: $($file.FullName)"
    }
    if ($Mode -eq 'Verify' -and $file.FullName -eq $mainPath) {
        if ($signature.SignerCertificate.Subject -cne $ExpectedPublisherSubject) {
            throw "The runtime publisher does not match ExpectedPublisherSubject."
        }
        if ($null -eq $signature.TimeStamperCertificate) {
            throw 'The runtime signature must have a trusted timestamp.'
        }
    }
}
if ($binaryCount -eq 0) { throw 'No Windows binaries found.' }
if ($Mode -eq 'Verify') {
    Write-Host "Verified embedded Code Signing signatures on $binaryCount runtime binaries."
}

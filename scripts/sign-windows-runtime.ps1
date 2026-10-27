# SPDX-FileCopyrightText: 2026 Leonardo Muffato (AUTOSOFT Engineering - www.autosoft-engineering.de)
# SPDX-License-Identifier: MIT

#Requires -Version 5.1

<#
.SYNOPSIS
Signs a built runtime before assembly using an existing Code Signing identity.
.DESCRIPTION
The certificate/private key must already be available in CurrentUser\My, for
example through a hardware token's provider. No key is exported or imported.
S/MIME and self-signed certificates are rejected. Valid upstream signatures are
preserved. The final signed runtime is verified before this script succeeds.
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)] [string]$RuntimePath,
    [Parameter(Mandatory = $true)] [ValidatePattern('^[a-fA-F0-9]{40}$')]
    [string]$CertificateThumbprint,
    [Parameter(Mandatory = $true)] [string]$SignToolPath,
    [Parameter(Mandatory = $true)] [uri]$TimestampServer
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
if ($env:OS -ne 'Windows_NT') { throw 'Windows code signing requires Windows.' }
Import-Module (Join-Path $PSHOME 'Modules\Microsoft.PowerShell.Security\Microsoft.PowerShell.Security.psd1')
if (-not [IO.Path]::IsPathRooted($SignToolPath) -or
    -not (Test-Path -LiteralPath $SignToolPath -PathType Leaf)) {
    throw 'Provide the absolute path to the installed Windows SDK signtool.exe.'
}
if (-not $TimestampServer.IsAbsoluteUri -or $TimestampServer.Scheme -ne 'https') {
    throw 'TimestampServer must be an absolute HTTPS RFC3161 endpoint.'
}
$certificate = Get-Item -LiteralPath "Cert:\CurrentUser\My\$CertificateThumbprint"
$eku = @($certificate.Extensions | Where-Object { $_.Oid.Value -eq '2.5.29.37' } |
    ForEach-Object { $_.EnhancedKeyUsages } | ForEach-Object { $_.Value })
if ($eku -notcontains '1.3.6.1.5.5.7.3.3') {
    throw 'A certificate for Code Signing is required; an S/MIME certificate cannot be used.'
}
if (-not $certificate.HasPrivateKey -or $certificate.Subject -eq $certificate.Issuer -or
    $certificate.NotBefore -gt (Get-Date) -or $certificate.NotAfter -le (Get-Date)) {
    throw 'Use a current Code Signing certificate with its private-key provider and a trusted issuer.'
}
$checker = Join-Path $PSScriptRoot 'check-windows-runtime-signatures.ps1'
$files = @(& $checker -RuntimePath $RuntimePath -Mode ListUnsigned -SignToolPath $SignToolPath)
foreach ($file in $files) {
    & $SignToolPath sign /sha1 $CertificateThumbprint /s My /fd SHA256 `
        /tr $TimestampServer.AbsoluteUri /td SHA256 $file
    if ($LASTEXITCODE -ne 0) { throw "Signing failed: $file" }
}
& $checker -RuntimePath $RuntimePath -ExpectedPublisherSubject $certificate.Subject `
    -SignToolPath $SignToolPath

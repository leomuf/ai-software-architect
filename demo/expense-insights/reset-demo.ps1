# SPDX-FileCopyrightText: 2026 Leonardo Muffato (AUTOSOFT Engineering - www.autosoft-engineering.de)
# SPDX-License-Identifier: MIT

#Requires -Version 5.1

<#
.SYNOPSIS
Removes only AI Software Architect artifacts generated inside this demo.
#>

[CmdletBinding(SupportsShouldProcess = $true, ConfirmImpact = "Medium")]
param()

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$DemoRoot = [IO.Path]::GetFullPath($PSScriptRoot)
$Target = [IO.Path]::GetFullPath((Join-Path $DemoRoot ".ai-architect"))

if ((Split-Path -Parent $Target) -ne $DemoRoot -or
    (Split-Path -Leaf $Target) -ne ".ai-architect") {
    throw "Refusing unexpected demo cleanup target: $Target"
}

if (-not (Test-Path -LiteralPath $Target)) {
    Write-Host "The demo is already clean."
    return
}

if ($PSCmdlet.ShouldProcess($Target, "remove generated demo architecture artifacts")) {
    Remove-Item -LiteralPath $Target -Recurse -Force
    Write-Host "Removed generated demo artifacts: $Target"
}

# SPDX-FileCopyrightText: 2026 Leonardo Muffato (AUTOSOFT Engineering - www.autosoft-engineering.de)
# SPDX-License-Identifier: MIT

<#
.SYNOPSIS
Runs the release-gate smoke test for the structured Codex plugin mention.

.DESCRIPTION
Delegates to the maintained Codex evaluation runner with its isolated smoke mode.
The result is never appended to the five-fixture exploratory performance ledger.
#>

[CmdletBinding()]
param(
    [string]$Model = "gpt-5.6-sol",
    [ValidateSet("standard", "fast", "unknown")]
    [string]$Speed = "standard",
    [string]$ExpectedPluginVersion,
    [ValidateSet("low", "medium", "high", "xhigh")]
    [string]$ReasoningEffort = "medium",
    [ValidateRange(1, 7200)]
    [int]$TimeoutSeconds = 600,
    [string]$OutputDirectory,
    [string]$CodexCommand,
    [switch]$DryRun
)

$ErrorActionPreference = "Stop"
$runner = Join-Path $PSScriptRoot "run-codex-exploratory-evaluations.ps1"
$arguments = @{
    ReleaseGateSmoke = $true
    Model = $Model
    Speed = $Speed
    ReasoningEffort = $ReasoningEffort
    TimeoutSeconds = $TimeoutSeconds
    DryRun = $DryRun
}
if ($ExpectedPluginVersion) {
    $arguments["ExpectedPluginVersion"] = $ExpectedPluginVersion
}
if ($OutputDirectory) {
    $arguments["OutputDirectory"] = $OutputDirectory
}
if ($CodexCommand) {
    $arguments["CodexCommand"] = $CodexCommand
}

& $runner @arguments

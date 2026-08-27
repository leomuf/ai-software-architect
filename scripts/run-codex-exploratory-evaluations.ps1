# SPDX-FileCopyrightText: 2026 Leonardo Muffato (AUTOSOFT Engineering - www.autosoft-engineering.de)
# SPDX-License-Identifier: MIT

<#
.SYNOPSIS
Runs the shared exploratory campaign through the Codex-specific Python runner.

.DESCRIPTION
This is a thin developer-facing entry point. It resolves Codex, selects an output
directory below .tmp/evaluations, and delegates all fixture and grading logic to
adapters/codex/evaluations.

.PARAMETER ExpectedPluginVersion
Optional release safety check. The runner detects the installed and enabled
AI Software Architect across all marketplaces, rejects ambiguous duplicates, and
exits before model calls if its version differs. PluginVersion remains a
backward-compatible alias.
#>

[CmdletBinding()]
param(
    [string[]]$Fixture,
    [string]$Campaign = "default",
    [string]$Model = "gpt-5.6-sol",
    [ValidateSet("standard", "fast", "unknown")]
    [string]$Speed = "standard",
    [Alias("PluginVersion")]
    [string]$ExpectedPluginVersion,
    [ValidateSet("low", "medium", "high", "xhigh")]
    [string]$ReasoningEffort = "medium",
    [ValidateRange(1, 7200)]
    [int]$TimeoutSeconds = 600,
    [string]$OutputDirectory,
    [string]$CodexCommand,
    [switch]$ContinueOnFailure,
    [switch]$ReleaseGateSmoke,
    [switch]$DryRun
)

$ErrorActionPreference = "Stop"
$repositoryRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path

function Write-EvaluationFailureDetails {
    param(
        [Parameter(Mandatory = $true)]
        [string]$EvidenceDirectory
    )

    $reportPath = Join-Path $EvidenceDirectory "report.json"
    if (-not (Test-Path -LiteralPath $reportPath -PathType Leaf)) {
        Write-Warning "No evaluation report was produced. Inspect the command output above."
        return
    }

    try {
        $report = Get-Content -LiteralPath $reportPath -Raw | ConvertFrom-Json
    }
    catch {
        Write-Warning "The evaluation report could not be read: $($_.Exception.Message)"
        return
    }

    Write-Host ""
    Write-Host "Evaluation failure details:" -ForegroundColor Red
    foreach ($result in @($report.results)) {
        if ($result.status -notin @("passed", "manual-review")) {
            Write-Host "- Fixture '$($result.fixture_id)' ($($result.scenario)): $($result.status)" `
                -ForegroundColor Red
        }
        if ($result.error) {
            Write-Host "  Runner error: $($result.error)" -ForegroundColor Red
        }

        foreach ($phase in @($result.phases)) {
            $failedAssertions = @($phase.assertions | Where-Object { $_.status -eq "fail" })
            if ($phase.exit_code -eq 0 -and $failedAssertions.Count -eq 0) {
                continue
            }

            Write-Host "  Phase '$($phase.name)' exited with code $($phase.exit_code)."
            foreach ($assertion in $failedAssertions) {
                Write-Host "  Failed check '$($assertion.name)': $($assertion.evidence)"
            }

            $messages = New-Object System.Collections.Generic.HashSet[string]
            if ($phase.event_log_file) {
                $eventLogPath = Join-Path `
                    (Join-Path $EvidenceDirectory "evidence\$($result.fixture_id)") `
                    $phase.event_log_file
                if (Test-Path -LiteralPath $eventLogPath -PathType Leaf) {
                    foreach ($line in Get-Content -LiteralPath $eventLogPath) {
                        try {
                            $event = $line | ConvertFrom-Json
                            if ($event.type -eq "error" -and $event.message) {
                                [void]$messages.Add([string]$event.message)
                            }
                            elseif ($event.type -eq "turn.failed" -and $event.error.message) {
                                [void]$messages.Add([string]$event.error.message)
                            }
                            elseif (
                                $event.type -eq "item.completed" -and
                                $event.item.type -eq "error" -and
                                $event.item.message
                            ) {
                                [void]$messages.Add([string]$event.item.message)
                            }
                        }
                        catch {
                            # Preserve the remaining diagnostics if one JSONL event is malformed.
                        }
                    }
                }
            }
            foreach ($message in $messages) {
                Write-Host "  Codex error: $message" -ForegroundColor Red
            }

            if ($phase.stderr_file) {
                $stderrPath = Join-Path `
                    (Join-Path $EvidenceDirectory "evidence\$($result.fixture_id)") `
                    $phase.stderr_file
                if (Test-Path -LiteralPath $stderrPath -PathType Leaf) {
                    $stderr = (Get-Content -LiteralPath $stderrPath -Raw).Trim()
                    if ($stderr) {
                        Write-Host "  Standard error: $stderr" -ForegroundColor Red
                    }
                }
            }
        }
    }

    Write-Host "Full report: $reportPath"
    Write-Host "Summary: $(Join-Path $EvidenceDirectory 'SUMMARY.md')"
}

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
    "--campaign", $Campaign,
    "--codex-command", $CodexCommand,
    "--model", $Model,
    "--speed", $Speed,
    "--reasoning-effort", $ReasoningEffort,
    "--timeout-seconds", $TimeoutSeconds.ToString()
)
$uvArguments = @()
if (-not $env:UV_CACHE_DIR) {
    $uvArguments += @("--cache-dir", (Join-Path $repositoryRoot ".uv-cache"))
}
if ($ExpectedPluginVersion) {
    $arguments += @("--expected-plugin-version", $ExpectedPluginVersion)
}
foreach ($fixtureId in $Fixture) {
    $arguments += @("--fixture", $fixtureId)
}
if ($ContinueOnFailure) {
    $arguments += "--continue-on-failure"
}
if ($ReleaseGateSmoke) {
    $arguments += "--release-gate-smoke"
}
if ($DryRun) {
    $arguments += "--dry-run"
}

if ($ReleaseGateSmoke) {
    Write-Host "Starting Codex structured plugin-invocation release-gate smoke test..."
}
else {
    Write-Host "Starting Codex exploratory evaluations..."
    Write-Host "Campaign: $Campaign"
}
Write-Host "Model: $Model ($ReasoningEffort reasoning)"
if ($ExpectedPluginVersion) {
    Write-Host "Expected plugin version: $ExpectedPluginVersion"
}
Write-Host "Evidence directory: $OutputDirectory"

Push-Location $repositoryRoot
try {
    & uv @uvArguments @arguments
    if ($LASTEXITCODE -ne 0) {
        $exitCode = $LASTEXITCODE
        Write-EvaluationFailureDetails -EvidenceDirectory $OutputDirectory
        throw "Codex exploratory evaluations failed with exit code $exitCode. Evidence: $OutputDirectory"
    }
}
finally {
    Pop-Location
}

Write-Host "Evaluation evidence: $OutputDirectory"

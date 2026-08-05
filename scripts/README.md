<!--
SPDX-FileCopyrightText: 2026 Leonardo Muffato (AUTOSOFT Engineering - www.autosoft-engineering.de)
SPDX-License-Identifier: MIT
-->

# Maintainer Scripts

These PowerShell scripts make the documented Codex plugin build and release
commands repeatable. Run them from a PowerShell terminal in the repository root.
They require Windows PowerShell 5.1 or later, `git`, and `uv`.

## PowerShell Execution Policy

Review scripts before running them, especially when they have changed. If
PowerShell reports that running scripts is disabled, inspect the effective
policies:

```powershell
Get-ExecutionPolicy -List
```

On a personal computer, prefer enabling signed remote scripts for only the
current user:

```powershell
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
```

This normally does not require Administrator rights. It is safer and narrower
than starting an elevated terminal and changing the default machine-wide scope.

For a single reviewed invocation without a persistent account-wide change, use
the process-scoped form:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\build-codex-plugin.ps1
```

Apply the same prefix to the other script and put its parameters after the
script path. `Bypass` applies only to that new PowerShell process, but it also
disables execution-policy checks there, so use it only for a script you have
reviewed. An organization-managed `MachinePolicy` or `UserPolicy` may still
prohibit either approach; do not override it—follow the administrator-approved
policy for that environment.

When `UV_CACHE_DIR` is not already configured, the scripts use the repository's
ignored `.uv-cache/` directory. An explicitly configured cache is preserved.

## Build and Validate the Codex Plugin

Build a new self-contained runtime, assign an automatic cache-busted development
version, validate the package, and smoke-test its short-lived hook runtime:

```powershell
.\scripts\build-codex-plugin.ps1
```

Build an exact version:

```powershell
.\scripts\build-codex-plugin.ps1 -PluginVersion 0.1.0-beta.1
```

For skill, reference, template, metadata, icon, or packaged-notice-only changes,
reuse the existing reviewed runtime:

```powershell
.\scripts\build-codex-plugin.ps1 -ReuseRuntime
```

Do not use `-ReuseRuntime` after runtime Python, shared domain code, schemas, dependencies,
`uv.lock`, Python, or PyInstaller configuration changes. When uncertain, use the
full build.

## Copy to the Personal Marketplace

Preview the exact destination and operation:

```powershell
.\scripts\copy-codex-plugin-to-personal-marketplace.ps1 -WhatIf
```

Validate and copy the package:

```powershell
.\scripts\copy-codex-plugin-to-personal-marketplace.ps1
```

The script checks the source package, the plugin name, and the existing default
personal-marketplace entry. It stages and validates a copy before replacing the
old package in `~/plugins/ai-software-architect`, restores the previous package
if replacement fails, and never edits `marketplace.json` or Codex's
installed-plugin cache. Codex resolves the built-in Personal marketplace's
`./plugins/...` source from the user profile even though its catalog is stored
under `~/.agents/plugins/marketplace.json`.

After it completes, use the Codex Desktop Plugins window to select **Install** or
**Update**, review and activate the hooks, and start a new task. The script does
not automate those user-controlled actions.

## Package an Installable Release

After building and validating an exact release version, wrap it in a local
repository marketplace that users can install without Python, `uv`, or project
dependencies:

```powershell
.\scripts\package-codex-release.ps1 -PluginVersion 0.1.0
```

The script checks that the assembled manifest version matches the requested
version, copies the plugin into a release-only marketplace layout, adds the
dependency-free installation guide, creates the Windows x86-64 ZIP, and writes
its SHA-256 checksum. It does not rebuild or revalidate the plugin runtime.

Generated output is written under `dist/release/` and remains ignored by Git.
Publish the ZIP and `SHA256SUMS.txt` as assets of the matching GitHub Release.
The versioned source inputs are:

- `adapters/codex/templates/marketplace.json`;
- `docs/INSTALL_CODEX_PLUGIN.md`; and
- `scripts/package-codex-release.ps1`.

## Run Deterministic Release-Candidate Gates

From a clean candidate commit:

```powershell
.\scripts\run-release-candidate-gates.ps1 -PluginVersion 0.1.0-beta.1
```

This checks the lockfile, synchronizes dependencies, verifies generated files,
runs linting, type checks, and tests, and performs a full build with package and
runtime validation. It also creates the dependency-free marketplace ZIP
and checksum. It stops immediately if tracked, staged, or untracked source
changes are present.

The script does not replace manual package inspection, the five exploratory Codex
fixtures, Codex Desktop install/update/uninstall acceptance, or clean-machine
acceptance. Follow the remaining gates in
[`docs/RELEASING.md`](../docs/RELEASING.md).

## Run Codex Exploratory Evaluations

Install the exact plugin candidate, review and activate its hooks, and then run the
five shared fixtures with the Codex-specific adapter:

```powershell
.\scripts\run-codex-exploratory-evaluations.ps1
```

Run the separate German-language campaign without changing the five-fixture English
baseline:

```powershell
.\scripts\run-codex-exploratory-evaluations.ps1 -Campaign german
```

It checks German clarification and focused comparison responses as well as the
corresponding clarification answer and approved ADR/artifact continuation.

Run the equivalent Brazilian Portuguese campaign independently:

```powershell
.\scripts\run-codex-exploratory-evaluations.ps1 -Campaign brazilian-portuguese
```

It checks Brazilian Portuguese clarification, focused comparison, clarification
continuation, and approved ADR/artifact persistence without changing the English or
German baselines.

Review two additional small Python repository structures without changing the
canonical five-fixture baseline:

```powershell
.\scripts\run-codex-exploratory-evaluations.ps1 -Campaign python-project-variety
```

This campaign compares proportionate read-only guidance for a cohesive single-file
CLI and a small multi-module `src`-layout service.

The runner defaults to `gpt-5.6-sol` with medium reasoning to keep the initial release
evaluation comparable. This is a maintainer test baseline, not a runtime plugin
requirement. When investigating a failed evaluation, you can rerun a single test
scenario, choose a different model, or save the results in a separate folder for
comparison:

```powershell
.\scripts\run-codex-exploratory-evaluations.ps1 `
  -Fixture architecture-option-comparison `
  -Model "gpt-5.6-sol" `
  -ReasoningEffort medium `
  -ExpectedPluginVersion 0.1.0 `
  -OutputDirectory .tmp\evaluations\release-candidate
```

For a real run, the runner asks Codex for the installed and enabled personal
plugin version and records it automatically. `-ExpectedPluginVersion` is an
optional release safety check: a mismatch stops the campaign before model calls.
It never installs, disables, or switches plugin versions. The former
`-PluginVersion` spelling remains a backward-compatible PowerShell alias.

Use `-Speed fast` to request Codex Fast mode explicitly. `-Speed standard` records
the intended standard baseline but cannot override a Fast preference already
persisted in the user's Codex configuration; confirm `/fast off` before that run.
Use `-Speed unknown` when the effective tier cannot be established rather than
mislabeling the observation.

Validate fixture discovery and report generation without invoking Codex or using
model credits:

```powershell
.\scripts\run-codex-exploratory-evaluations.ps1 -DryRun
```

The command writes `report.json`, `SUMMARY.md`, JSONL events, stderr, final
responses, isolated synthetic repositories, and repository-change evidence below
`.tmp/evaluations/` or the selected output directory. These generated files are
ignored by Git. If the campaign fails, the PowerShell entry point prints the
affected fixture and phase, failed checks, underlying Codex or stderr messages,
and direct paths to the full report and summary before exiting. During execution,
live `[current/total]` messages identify the active fixture and phase. A
`manual-review` result means the deterministic safeguards passed; it is not a
semantic pass. Review every expected and forbidden behavior before release.

See the [Codex runner documentation](../adapters/codex/evaluations/README.md) and
the [shared fixture contract](../shared/evaluations/README.md) for the architectural
separation.

## Maintain Exploratory Performance History

Every real campaign launched by `run-codex-exploratory-evaluations.ps1` now records
eligible completed fixtures in `evaluation-data/exploratory-runs.jsonl`
automatically. No additional import command is required. Dry runs and unusable
phases are excluded.

Archived or interactive Codex Desktop tasks require a review because a timestamp
cannot prove that the plugin actually produced a usable architecture response.
Export candidates first:

```powershell
.\scripts\export-codex-exploratory-history.ps1 `
  -Output .tmp\evaluations\history\candidates.json
```

Create a structured draft:

```powershell
.\scripts\draft-codex-exploratory-history-review.ps1 `
  -Export .tmp\evaluations\history\candidates.json `
  -ReviewerSessionId <reviewing-codex-task-id> `
  -Output .tmp\evaluations\history\review.json
```

The draft intentionally labels complete candidates `needs-review`. Ask Codex or a
human reviewer to inspect the bounded response evidence, confirm fixture and phase
mapping, and record `accepted` or `excluded`, a concise reason, and confidence.
Do not approve an interrupted task or a response that only reports inactive hooks,
plugin startup failure, cancellation, or another prerequisite failure.

After reviewing the entire batch, apply it idempotently:

```powershell
.\scripts\apply-codex-exploratory-history-review.ps1 `
  -Review .tmp\evaluations\history\review.json
```

Earlier machine-readable runner reports can be previewed and, after review,
imported once:

```powershell
.\scripts\import-exploratory-performance-reports.ps1
.\scripts\import-exploratory-performance-reports.ps1 -Apply
```

Render the complete history as a console table plus Markdown, primary CSV,
telemetry CSV, privacy-preserving tool-timeline CSV, recommendation-consistency
CSV, and JSON files:

```powershell
.\scripts\show-exploratory-performance.ps1
```

The command prints the generated output directory. Missing continuations appear as
an em dash and are excluded from continuation statistics. The report provides both
a broad cross-version fixture overview and strict like-for-like comparable groups.
After five exact release-compatible observations, it also renders informational
P50/P90 objective results. These warnings are separated by plugin version and never
fail the script or CI; P90 remains provisional until ten observations exist.
For comparison fixtures recorded with performance schema `1.3.0`, the report also
shows exact like-for-like selection distributions and assumption-fingerprint
consistency without retaining free-form assumption or repository text. Schema
`1.4.0` observations also show median visible comparison-response words and sample
coverage, without storing response content.
GitHub CI uses the same renderer for its Job Summary and uploads the Markdown,
primary CSV, telemetry CSV, tool-timeline CSV, recommendation-consistency CSV, and
JSON report files as an
artifact; it never
modifies the canonical ledger.

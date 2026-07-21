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

The runner defaults to `gpt-5.6` with medium reasoning to keep the initial release
evaluation comparable. This is a maintainer test baseline, not a runtime plugin
requirement. When investigating a failed evaluation, you can rerun a single test
scenario, choose a different model, or save the results in a separate folder for
comparison:

```powershell
.\scripts\run-codex-exploratory-evaluations.ps1 `
  -Fixture architecture-option-comparison `
  -Model "gpt-5.6" `
  -ReasoningEffort medium `
  -PluginVersion 0.1.0 `
  -OutputDirectory .tmp\evaluations\release-candidate
```

Validate fixture discovery and report generation without invoking Codex or using
model credits:

```powershell
.\scripts\run-codex-exploratory-evaluations.ps1 -DryRun
```

The command writes `report.json`, `SUMMARY.md`, JSONL events, stderr, final
responses, isolated synthetic repositories, and repository-change evidence below
`.tmp/evaluations/`. These generated files are ignored by Git. A
`manual-review` result means the deterministic safeguards passed; it is not a
semantic pass. Review every expected and forbidden behavior before release.

See the [Codex runner documentation](../adapters/codex/evaluations/README.md) and
the [shared fixture contract](../shared/evaluations/README.md) for the architectural
separation.

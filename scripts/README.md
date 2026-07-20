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
version, validate the package, and smoke-test its MCP and hook runtime:

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

Do not use `-ReuseRuntime` after runtime Python, MCP code, schemas, dependencies,
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

## Run Deterministic Release-Candidate Gates

From a clean candidate commit:

```powershell
.\scripts\run-release-candidate-gates.ps1 -PluginVersion 0.1.0-beta.1
```

This checks the lockfile, synchronizes dependencies, verifies generated files,
runs linting, type checks, and tests, and performs a full build with package and
runtime validation. It stops immediately if tracked, staged, or untracked source
changes are present.

The script does not replace manual package inspection, the five exploratory Codex
fixtures, Codex Desktop install/update/uninstall acceptance, or clean-machine
acceptance. Follow the remaining gates in
[`docs/RELEASING.md`](../docs/RELEASING.md).

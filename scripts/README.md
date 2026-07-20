<!--
SPDX-FileCopyrightText: 2026 Leonardo Muffato (AUTOSOFT Engineering - www.autosoft-engineering.de)
SPDX-License-Identifier: MIT
-->

# Maintainer Scripts

These PowerShell scripts make the documented Codex plugin build and release
commands repeatable. Run them from a PowerShell terminal in the repository root.
They require Windows PowerShell 5.1 or later, `git`, and `uv`.

Review scripts before running them, especially when they have changed. If the
current execution policy permits local scripts, use the short commands below. If
PowerShell reports that script execution is disabled, use the process-scoped form
shown next; it does not change machine-wide or account-wide policy:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\build-codex-plugin.ps1
```

Apply the same prefix to the other script and put its parameters after the
script path. An organization-managed policy may still prohibit this; follow the
policy approved for that environment rather than changing it.

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
old package, restores the previous package if replacement fails, and never edits
`marketplace.json` or Codex's installed-plugin cache.

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

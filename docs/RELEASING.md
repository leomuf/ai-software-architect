<!--
SPDX-FileCopyrightText: 2026 Leonardo Muffato (AUTOSOFT Engineering - www.autosoft-engineering.de)
SPDX-License-Identifier: MIT
-->

# Releasing AI Software Architect

This is the canonical maintainer guide for preparing, validating, testing, and
publishing the Codex plugin through GitHub. It documents the current repository
behavior as well as the manual gates that remain necessary before a release.

The initial supported package is Windows x86-64. Future coding-agent adapters and
operating-system packages require their own validated release procedures.

## PowerShell Execution Policy

If PowerShell reports that running scripts is disabled, inspect the effective
policies first:

```powershell
Get-ExecutionPolicy -List
```

On a personal computer, prefer a user-scoped setting:

```powershell
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
```

This normally does not require Administrator rights and does not alter the
machine-wide policy. Review repository scripts before running them. Do not
override an organization-managed `MachinePolicy` or `UserPolicy`; follow the
policy approved by the administrator for that environment. A temporary,
process-scoped alternative is documented in
[`scripts/README.md`](../scripts/README.md#powershell-execution-policy).

## Release Documentation Map

| Concern | Canonical location |
|---|---|
| User overview and local development quick start | [`README.md`](../README.md) |
| Repeatable local build and release commands | [`scripts/README.md`](../scripts/README.md) |
| Open release work | [`TODO.md`](../TODO.md) |
| Changes intended for users | [`CHANGELOG.md`](../CHANGELOG.md) |
| Pull-request and `main` validation | [`.github/workflows/ci.yml`](../.github/workflows/ci.yml) |
| Tag-triggered package build | [`.github/workflows/release.yml`](../.github/workflows/release.yml) |
| Concise GitHub and Devpost release procedure | [`ReleaseGuide.md`](ReleaseGuide.md) |
| Dependency-free installation | [`INSTALL_CODEX_PLUGIN.md`](INSTALL_CODEX_PLUGIN.md) |
| Scenario-to-gate mapping | [`shared/evaluations/verification-manifest.yaml`](../shared/evaluations/verification-manifest.yaml) |
| Five exploratory fixtures | [`shared/evaluations/model-fixtures/`](../shared/evaluations/model-fixtures/) |
| Codex exploratory runner | [`adapters/codex/evaluations/`](../adapters/codex/evaluations/README.md) |
| Future exploratory-test automation | [`shared/evaluations/release-automation-plan.md`](../shared/evaluations/release-automation-plan.md) |
| Per-release evidence | Copy [`release-evidence-template.md`](release-evidence-template.md) to `docs/releases/<version>.md` |

## Current GitHub Workflow Behavior

The existing `Release artifact` workflow is defined in
[`.github/workflows/release.yml`](../.github/workflows/release.yml).

It currently:

1. starts automatically when a tag matching `v*` is pushed;
2. derives the plugin version from that tag;
3. builds the self-contained Windows x86-64 plugin with that exact version;
4. validates and smoke-tests the assembled package;
5. creates an installable repository marketplace ZIP and SHA-256 checksum; and
6. uploads them as GitHub Actions artifacts.

It currently does **not**:

- support `workflow_dispatch` for a manual run;
- execute all deterministic CI gates;
- create a build attestation;
- create a public GitHub Release; or
- attach the ZIP and checksum to a GitHub Release.

The uploaded artifact is a release candidate until the remaining manual gates
pass and a maintainer attaches the inner release ZIP and checksum to a reviewed
GitHub Release. Follow [`ReleaseGuide.md`](ReleaseGuide.md) for that procedure.

## Version Policy

Use Semantic Versioning for public packages:

- first beta: `0.1.0-beta.1`;
- first stable release: `0.1.0`;
- local iteration: `0.1.0+codex.<UTC timestamp>`.

The Git tag adds a `v`, for example `v0.1.0-beta.1`; the plugin manifest does not.

Supply the complete version to `scripts/build-codex-plugin.ps1` during assembly.
Never edit the generated manifest or recalculate provenance after the build. Any
post-build mutation must make validation fail.

## Prepare the Candidate Commit

Before building a release candidate:

1. Update [`CHANGELOG.md`](../CHANGELOG.md).
2. Review [`TODO.md`](../TODO.md) and leave every unproven gate unchecked.
3. Confirm that generated schemas, acceptance criteria, and third-party notices are
   current.
4. Confirm that the candidate commit is reviewed and its CI and CodeQL checks pass.
5. Start from a clean working tree:

```powershell
git status --short
```

Do not build a release candidate from uncommitted or untracked source changes.

## Build a Local Development Package

From the repository root, run:

```powershell
.\scripts\build-codex-plugin.ps1
```

The script synchronizes the locked environment, creates a unique UTC
cache-busted version, performs a full runtime build, validates the assembled
package and provenance, and smoke-tests the packaged short-lived hook surface.
The assembled package is written to:

```text
dist/codex/ai-software-architect/
```

The build script safely replaces only that expected generated directory.

### Reuse an Existing Runtime for a Fast Rebuild

Reuse the reviewed runtime only when none of these changed:

- `adapters/codex/runtime_entry.py`;
- `adapters/codex/hook_entry.py`;
- `adapters/codex/artifact_guard.py`;
- `adapters/codex/control_plane.py`;
- `tools/python-mcp/`;
- `shared/schemas/`;
- runtime dependencies or `uv.lock`; or
- the Python/PyInstaller build configuration.

For skill, reference, template, plugin-metadata, icon, or packaged-notice-only
changes:

```powershell
.\scripts\build-codex-plugin.ps1 -ReuseRuntime
```

If there is any doubt, perform the full `--build-runtime` build. Do not run a
post-build cachebuster tool against the assembled directory because that would
invalidate its provenance hashes.

Pure repository-documentation changes such as `README.md` or files under `docs/`
do not require a plugin rebuild because those files are not packaged.

## Validate the Assembled Package

`build-codex-plugin.ps1` always runs package/provenance validation and a runtime
smoke test after either build mode. A failed check stops the script, and the
package must not be copied into a marketplace.

## Copy a Development Package to the Personal Marketplace

The default personal marketplace is:

```text
~/.agents/plugins/marketplace.json
```

Its AI Software Architect entry should resolve
`./plugins/ai-software-architect`, making the package target:

```text
~/plugins/ai-software-architect/
```

Preview the exact destination and operation without changing marketplace files:

```powershell
.\scripts\copy-codex-plugin-to-personal-marketplace.ps1 -WhatIf
```

Then validate, stage, and replace the development package:

```powershell
.\scripts\copy-codex-plugin-to-personal-marketplace.ps1
```

The script validates the source package, plugin name, catalog entry, exact
destination, and a staged copy before replacement. If replacement fails after
the old package was moved, it restores that package. It does not edit
`marketplace.json`, install the plugin, activate hooks, or modify Codex's
installed-plugin cache.

If the personal marketplace does not exist, create it through Codex's
`$plugin-creator` workflow instead of hand-editing global configuration. See the
official [Build plugins](https://learn.chatgpt.com/docs/build-plugins#build-your-own-curated-plugin-list)
documentation.

## Install or Update from the Codex Plugins Window

After copying the package:

1. Open **Plugins** in Codex Desktop.
2. Select the **Personal** marketplace.
3. Open **AI Software Architect**.
4. Select **Install** if it is not installed, or **Update** when Codex detects the
   new cache-busted version.
5. Review the bundled hook definitions and activate them from the plugin page.
6. Start a new task before testing the updated skill and hooks.
7. Confirm that the displayed plugin version equals the version just built.

If **Update** is not shown:

1. verify the version in
   `~/plugins/ai-software-architect/.codex-plugin/plugin.json`;
2. confirm that it differs from the installed version;
3. refresh or restart Codex Desktop; and
4. reopen the plugin from the **Personal** marketplace.

Do not edit Codex's installed-plugin cache. A clean reinstall through the Plugins
window may be used when the release gate specifically requires it.

## Build the Exact Release Candidate

Use the intended public version without development build metadata:

```powershell
.\scripts\build-codex-plugin.ps1 -PluginVersion 0.1.0-beta.1
```

Use this exact package for every remaining release gate. Do not rebuild between
testing and publication.

## Exact Release-Candidate Gates

### Gate A: Deterministic Repository Validation

Run from a clean candidate commit:

```powershell
.\scripts\run-release-candidate-gates.ps1 -PluginVersion 0.1.0-beta.1
```

The script verifies that the candidate tree is clean, checks and synchronizes the
lockfile, regenerates and compares derived artifacts, runs linting, type checks,
and tests, performs a full build, package validation, and runtime smoke test,
then creates the dependency-free marketplace ZIP and checksum. All checks
must succeed. Gates B-E remain explicit manual procedures because they require
human inspection, the Codex model and Desktop UI, or a clean machine.

### Gate B: Package Inspection

Confirm:

- the manifest and provenance contain the intended release version;
- every provenance hash validates;
- the archive contains `LICENSE`, `NOTICE`, and `THIRD_PARTY_NOTICES.md`;
- the package contains no `.venv`, `uv`, build cache, source credential, or
  unresolved placeholder;
- the manifest contains no `mcpServers` entry or `.mcp.json` companion;
- every hook invokes the fixed bundled short-lived runtime with `--codex-hook`; and
- the runtime starts without installing or downloading dependencies.

### Gate C: Five Exploratory Fixtures

Run all fixtures named by
[`verification-manifest.yaml`](../shared/evaluations/verification-manifest.yaml):

1. `clarify-ui-architecture.yaml`
2. `architecture-option-comparison.yaml`
3. `read-only-architecture-review.yaml`
4. `abstract-factory-example.yaml`
5. `avoid-overengineering.yaml`

After installing the exact candidate and activating its reviewed hooks, run:

```powershell
.\scripts\run-codex-exploratory-evaluations.ps1 `
  -ExpectedPluginVersion 0.1.0 `
  -Model gpt-5.6-sol `
  -ReasoningEffort medium
```

Store the generated output path in the release evidence. The runner creates one
isolated synthetic Git repository per fixture, captures Codex JSONL and final
responses, checks deterministic policies, and exercises the approval continuation.
It queries all marketplaces, requires exactly one installed and enabled matching plugin,
and records its plugin ID, marketplace, version, and available provenance digest. The
expected-version argument fails before model calls if another version is active, while
duplicate enabled installations fail as ambiguous before any evaluation credits are used.
It does not install or switch plugin versions.
It does not perform semantic grading. A `manual-review` status requires a human to
assess every expected and forbidden behavior before recording the gate as passed.

The `gpt-5.6-sol` and medium settings below pin the initial release-evaluation baseline
for comparable evidence. They do not constrain the model a user may select when
running the installed plugin.

For the initial beta:

- use `gpt-5.6-sol` with medium reasoning;
- let the runner isolate each independent fixture and preserve the one session
  needed for the approval continuation;
- install the exact release-candidate plugin, then invoke
  `$ai-software-architect` directly for every fixture; do not add an `@` plugin
  mention;
- assess every expected and forbidden behavior;
- record repository status and side effects;
- do not retry a behavioral failure merely to obtain a better answer; and
- record the exact Codex and plugin versions.

### Gate D: Manual Codex Desktop Acceptance

This gate is required even after future model-evaluation automation exists:

1. Install or update the exact candidate through the Plugins window.
2. Review and activate its current hook definitions.
3. Confirm the single `$ai-software-architect` skill covers focused help and the
   complete lifecycle without an `@` plugin mention.
4. Confirm hook-based contract validation and secret scanning in at least one approved artifact workflow.
5. Run the candidate from multiple tasks.
6. Keep Codex Desktop open and uninstall on the first attempt.
7. Confirm that no plugin runtime process or stale installed package remains.
8. Reinstall once and confirm the same version and hook-review behavior.

If first-attempt uninstall fails, capture the Codex version, plugin version, active
tasks, process ownership, elapsed time, and recovery steps. The release remains
blocked; the Codex package is already designed without persistent MCP registration.

### Gate E: Clean-Machine Acceptance

On a clean Windows x86-64 environment without Python, `uv`, or development caches:

1. install the exact package;
2. activate the reviewed hooks;
3. run one main workflow and one approved artifact write that exercises deterministic pre-write validation;
4. verify that no first-run download or network listener appears; and
5. uninstall successfully on the first attempt.

## Record Release Evidence

Copy [`release-evidence-template.md`](release-evidence-template.md) to:

```text
docs/releases/<version>.md
```

Complete a working copy during Gates A–E without changing the candidate commit.
Attach the sanitized result to the GitHub Release or include it in the release notes.
If the project also keeps the record under `docs/releases/`, commit that copy after
the release tag in a documentation-only commit and link it back to the immutable tag.
Never rebuild or retag merely to add evidence, and never include credentials, hidden
reasoning, unnecessary repository content, or sensitive local paths.

Step 5—the manual Codex Desktop acceptance procedure—belongs here because it is a
maintainer release gate. Its result belongs in the per-version release evidence
record, not in the README.

## Publish Through GitHub

The intended future automated flow is:

1. merge the approved candidate commit;
2. confirm required CI and CodeQL checks;
3. create the annotated tag, for example `v0.1.0-beta.1`;
4. build the immutable package from that tag and record its checksum and provenance;
5. create a GitHub prerelease;
6. attach the ZIP, checksum, provenance/evidence summary, and release notes; and
7. verify installation from the published distribution path.

Until `.github/workflows/release.yml` creates the GitHub Release, publish its
tag-versioned artifact manually only after the recorded gates pass. Confirm the
manifest version and release evidence before publishing.

## Release Decision

A release is ready only when:

- the candidate commit and working tree are identified;
- Gates A–E pass;
- every critical expected/forbidden fixture behavior passes;
- no infrastructure result is unresolved;
- first-attempt uninstall passes;
- release notes and support information are public; and
- one maintainer records the final go/no-go decision.

Any failed security, provenance, lifecycle, or destructive-side-effect gate blocks
the release.

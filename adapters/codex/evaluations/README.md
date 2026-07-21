<!--
SPDX-FileCopyrightText: 2026 Leonardo Muffato (AUTOSOFT Engineering - www.autosoft-engineering.de)
SPDX-License-Identifier: MIT
-->

# Codex Exploratory Evaluation Runner

This directory contains the Codex-specific adapter for executing the shared
exploratory fixtures. It invokes the stable non-interactive `codex exec` surface,
captures its JSONL events and final response, and applies deterministic safeguards.

The runner does not contain the test cases themselves. Those platform-neutral
definitions live in [`shared/evaluations`](../../../shared/evaluations/README.md), so
future GitHub Copilot, Claude Code, and Antigravity adapters can reuse them.

## Safety and execution model

- Every fixture runs in a newly initialized synthetic Git repository.
- Initial turns use Codex's read-only sandbox.
- Runs without a continuation use `--ephemeral` and do not persist a Codex session.
- A continuation fixture must retain its first session so `codex exec resume` can
  test the real follow-up behavior. Its continuation uses `workspace-write` only in
  the synthetic repository.
- Raw JSONL, stderr, final responses, deterministic assertions, and repository
  changes are written below the chosen output directory.
- Semantic expectations remain explicit manual-review items. The runner never
  converts missing semantic evidence into a pass.

The runner uses the caller's existing Codex authentication and installed plugin.
Install the exact release candidate and activate its reviewed hooks before running
the campaign. For real runs, it searches every marketplace, requires exactly one
installed and enabled AI Software Architect, and records its plugin ID, marketplace,
version, and available provenance digest. An optional expected version acts only as
an early mismatch guard. The runner does not install, update,
switch, trust, disable, or uninstall a plugin.

Use the repository-level PowerShell entry described in
[`scripts/README.md`](../../../scripts/README.md#run-codex-exploratory-evaluations).

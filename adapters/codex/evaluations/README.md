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

## Performance history

Real runner campaigns normalize every eligible completed fixture into the shared
append-only ledger at `evaluation-data/exploratory-runs.jsonl`. The runner records
initial and continuation time separately, campaign wall-clock time, fixture and
workload hashes, model, reasoning effort, speed, Codex and plugin versions, Git
commit, and host class. Dry runs and infrastructure failures never enter the
ledger. Repeated recording is content-addressed and idempotent.

Schema `1.1.0` observations may also contain runner-observed Codex telemetry:
first JSONL event, first and last completed agent-message event, item and tool-call
counts, and input/cached-input/output tokens when Codex reports them. These event
times are not time-to-first-token. Codex currently does not expose separate hook,
template-loading, patch-construction, or subagent-duration timings; the runner
records those fields as unavailable and never estimates them. Legacy schema
`1.0.0` observations remain valid and retain their content-addressed identities.
Schema `1.2.0` adds the privacy-preserving tool timeline described below. Schema
`1.3.0` can additionally retain a validated comparison's public selected category
and canonical name plus a normalized SHA-256 fingerprint and word count for its
material assumption. It never copies the free-form assumption or a project-specific
no-pattern label into the versioned ledger.

Four focused modules keep responsibilities separate:

- `performance_models.py` defines the strict canonical Pydantic contracts;
- `performance_ledger.py` provides validated, locked, atomic JSONL updates;
- `performance_import.py` migrates earlier machine-readable runner reports;
- `performance_report.py` produces stable Markdown, CSV, and JSON tables and
  like-for-like grouped statistics.

The report uses median (P50), P75, P90, median absolute deviation (MAD), and the
P90-P50 tail gap as its primary cross-version latency indicators. Mean, sample
standard deviation, minimum, and maximum remain available in comparable-group
details and JSON for diagnosis. P90 is provisional below ten samples, and groups
below five samples are descriptive rather than decision-grade.

Report schema `1.5.0` also evaluates fixed warning-only latency objectives for
exact release-compatible cohorts: plugin version, fixture revision, workload,
model, reasoning effort, speed, and execution mode must all match. An objective
appears only at five observations, labels P90 provisional below ten, and never
changes the report or CI exit code. Records whose plugin version is unknown are
excluded from this release-specific section.

`observed-total` is the sum of phases actually measured for an observation.
`completed-workflow-total` is reported only when both the initial and continuation
phases completed. This prevents an initial-only interaction from appearing to be a
fast end-to-end workflow. The `Samples/Runs` coverage column makes missing
continuations visible and never treats them as zero.

The renderer writes `performance-telemetry.csv` alongside the primary Markdown,
CSV, and JSON reports. The Markdown report includes a runner-observed telemetry
section, while `performance.json` exposes the same rows under
`subphase_telemetry`. Schema `1.2.0` observations also retain a
privacy-preserving tool timeline. `performance-tool-timeline.csv`, the Markdown
timeline, and `performance.json` record only tool category, order, relative
start/end/duration, gap, and status. They never copy commands, paths, prompts,
source text, or tool output.

The Markdown and JSON reports, plus `recommendation-consistency.csv`, group captured
decisions only when fixture revision, workload, installed plugin version and
provenance, model, reasoning effort, speed, and execution mode match exactly. They
distinguish a stable selection, changed
selections with different or rephrased assumptions, and a contradiction candidate
where one identical assumption fingerprint maps to different selections. These are
review signals, not automated semantic verdicts.

`historical_review.py` is deliberately separate. It uses the documented local
Codex App Server to export Desktop task evidence, but never automatically treats a
completed status as semantic approval. A Codex-assisted or human review must record
the fixture, phase, eligibility, reason, confidence, and evidence hash before an
archived task can be added to the canonical history. Full task transcripts and
hidden reasoning are not versioned.

<!--
SPDX-FileCopyrightText: 2026 Leonardo Muffato (AUTOSOFT Engineering - www.autosoft-engineering.de)
SPDX-License-Identifier: MIT
-->

# Exploratory Evaluation Performance History — Implementation Plan

## Status

**Implementation in progress — canonical history, historical migration, automatic
runner recording, local reports, and non-mutating CI presentation are implemented.**

This is the durable working plan for collecting, preserving, reporting, and later
comparing the execution time of exploratory evaluations. Keep it current until every
acceptance criterion below is implemented and verified. Check an item only after its
code, tests, and documentation are complete.

The plan complements:

- [`../shared/evaluations/README.md`](../shared/evaluations/README.md), which owns the
  platform-neutral exploratory fixtures;
- [`../adapters/codex/evaluations/README.md`](../adapters/codex/evaluations/README.md),
  which describes Codex-specific execution;
- [`../shared/evaluations/release-automation-plan.md`](../shared/evaluations/release-automation-plan.md),
  which describes possible protected release automation.

## Objective

Create one auditable performance history for:

1. completed historical exploratory tests stored as Codex tasks;
2. future campaigns launched interactively in Codex;
3. future campaigns launched through
   `scripts/run-codex-exploratory-evaluations.ps1`;
4. local tabular reports and GitHub Actions summaries that compare releases using
   statistically meaningful, like-for-like measurements.

The implementation must preserve incomplete historical evidence. If an early test
has an initial response but no user approval or continuation, the initial phase is
recorded and the continuation remains explicitly missing. Missing durations must
never be treated as zero.

Tests that did not reach a usable result are not performance observations. Runs
aborted because hooks were not activated, the expected plugin was unavailable,
startup or authentication failed, a transport closed, the user cancelled the task,
or another infrastructure prerequisite was missing must be excluded from the
canonical performance ledger and all statistics. Preserve their task IDs and
exclusion reasons only in the migration or campaign import report so the historical
review remains auditable.

## Architectural Decision

Use an append-only, versioned **JSON Lines (JSONL) ledger** as the canonical data
source. Do not use a binary database as the source of truth.

Reasons:

- JSONL produces reviewable Git diffs and is straightforward to process in CI;
- individual observations can be appended without rewriting an opaque database;
- schema validation and deterministic duplicate detection remain simple;
- CSV, Markdown, HTML, SQLite, or DuckDB views can be generated when needed.

A generated local database may later be added as a disposable query cache. It must
always be reproducible from the canonical ledger and must not be versioned.

## Proposed Repository Structure

```text
evaluation-data/
    README.md
    exploratory-performance.schema.yaml
    exploratory-runs.jsonl
    historical-import-overrides.yaml
    imports/
        codex-desktop-history-review.json
        existing-runner-reports-import.json
adapters/codex/evaluations/
    performance_models.py
    performance_ledger.py
    performance_import.py
    historical_review.py
    performance_report.py
scripts/
    export-codex-exploratory-history.ps1
    draft-codex-exploratory-history-review.ps1
    apply-codex-exploratory-history-review.ps1
    import-exploratory-performance-reports.ps1
    show-exploratory-performance.ps1
```

Run-specific raw events and generated reports continue to live below `.tmp/` and
remain unversioned. The ledger stores bounded measurements and provenance, not full
prompts, responses, hidden reasoning, credentials, or sensitive local paths.

## Canonical Record Shape

Implement the contract as strict Pydantic models and a corresponding YAML schema.
The exact field names may be refined during implementation, but the information and
null semantics below are required.

```yaml
schema_version: 1.0.0
record_id: stable-content-derived-id

campaign:
  id: Run15
  execution_mode: parallel-codex-tasks
  started_at: 2026-07-21T18:30:00Z
  completed_at: 2026-07-21T18:34:00Z
  wall_clock_seconds: 240.0

test:
  fixture_id: architecture-option-comparison
  fixture_revision: sha256-of-effective-fixture
  workload_fingerprint: sha256-of-representative-project
  task_name: Run15_Exploratory2
  task_id: 019f...

runtime:
  model: gpt-5.6-sol
  reasoning_effort: medium
  speed: standard
  codex_version: unknown
  plugin_version: 0.1.0
  plugin_provenance: sha256:...
  git_commit: 8f2f...

phases:
  initial:
    status: completed
    duration_seconds: 31.375
  continuation:
    status: not-run
    duration_seconds: null

timing:
  measured_phase_seconds: 31.375

result:
  outcome: manual-review
  source: codex-task-history
  measurement_quality: reconstructed
  notes: Continuation was not requested in this campaign.
```

### Required semantics

- Store unavailable numeric values as JSON `null`, never `NaN`, zero, or `"-"`.
- Render a missing value as an em dash in human-readable tables.
- Use `speed: standard`, `fast`, or `unknown`; speed is distinct from reasoning
  effort.
- Use `execution_mode` to distinguish sequential CLI runs from parallel Codex tasks.
- Preserve both campaign wall-clock duration and the sum of measured phase durations.
- Record `measured`, `reconstructed`, or `inferred` measurement quality.
- Never infer an unknown model, speed, plugin version, or Codex version without
  evidence. Use `unknown` and optionally a bounded note.
- Use stable record IDs so importing the same task or report again is idempotent.
- Include the effective fixture hash because timings for changed workloads are not
  directly comparable.

### Eligibility rules

A test or phase is eligible for performance history only when:

- the expected plugin and required hooks were active before measured work began;
- the intended prompt reached the model and produced a completed, usable response;
- the result was not terminated by cancellation, timeout, transport failure,
  authentication failure, process failure, or missing runtime prerequisites;
- its start and completion timestamps are trustworthy;
- the measured interval represents the intended test rather than setup, approval,
  installation, or recovery work.

An absent continuation is not automatically a failed or aborted test. If the initial
phase completed successfully and the historical campaign simply did not ask for a
user decision, record the initial phase and leave the continuation `not-run` with a
null duration. If a continuation was started but aborted, exclude that continuation
from performance statistics; retain only an independently completed initial phase.

Do not calculate a campaign performance total from excluded or aborted phases. A
campaign may still contribute its independently completed tests, but it must be
marked as incomplete and must not be presented as a complete five-test campaign.

## Historical Codex Task Migration

### Codex-assisted review

The historical Desktop migration is a one-time evidence-review workflow, not only a
title parser. Codex must use its task-history capabilities to inspect each readable
archived task and produce a structured assessment that later evaluation tooling can
consume.

Keep two kinds of evidence separate:

1. **Deterministic observations** extracted from the task record, such as task and
   turn IDs, titles, timestamps, duration, completion state, and available runtime
   metadata.
2. **Semantic review decisions** made by Codex, such as fixture mapping, phase
   mapping, whether a response is usable, whether a run stopped because hooks were
   inactive, and whether an apparent continuation belongs to the same test.

Codex must not rewrite measured timestamps or infer missing model and speed values.
Every semantic decision must include a short reason, confidence level, and bounded
evidence reference. Ambiguous decisions require human approval before they enter the
canonical performance ledger.

The review output must be saved in a structured, schema-validated import batch before
canonical records are appended. At minimum, preserve:

- reviewing Codex task/session ID and review timestamp;
- source task ID, title, and source turn IDs;
- detected campaign, fixture, and phase;
- measured start, completion, and duration values;
- eligibility or exclusion decision and reason;
- semantic-review confidence;
- known model, reasoning effort, speed, plugin version, and Codex version, with
  `unknown` where the source does not establish them;
- a content or evidence hash that detects later source or review changes;
- the resulting canonical record ID, when accepted.

Do not store hidden reasoning or unnecessary full task transcripts in the versioned
history. Bounded evidence excerpts may be retained when needed to justify a mapping
or exclusion and when they contain no sensitive repository content.

Later evaluations consume the accepted canonical JSONL records as historical
baselines. They must not rerun or reinterpret archived tasks during every report.
If a historical review is corrected, append or apply a traceable reviewed correction
rather than silently changing its meaning.

### Discovery and grouping rules

The importer must tolerate historical title variants such as:

- `Run14_Exploratory2`
- `run14_Exploratory_2`
- `Run 14 Exploratory 2`
- `Exploratory2`
- `Exploratory 2`

Grouping order:

1. Prefer an explicit run number in the normalized title.
2. For early unnumbered tasks, cluster candidates using their start timestamps and
   the expected exploratory fixture set.
3. Validate the proposed group against prompt content and chronological order.
4. Assign a confidence level and require human review for ambiguous groups.
5. Allow corrections through `historical-import-overrides.yaml` rather than
   hard-coding exceptions in the importer.

### Phase reconstruction rules

- Map the original prompt and its completed response to the initial phase.
- Map an explicit user approval, revision, or information request and its completed
  response to the continuation phase.
- If no such follow-up exists, store `status: not-run` and `duration_seconds: null`.
- Calculate a phase duration from its own start and completion timestamps; do not
  use a task's last-updated timestamp.
- Do not count subagent work as a separate exploratory fixture. Its time remains part
  of the parent phase when already included in the parent duration.
- Do not store an interrupted or still-running phase as completed.
- Exclude tasks that stopped before a usable response because hooks were inactive,
  plugin activation failed, Codex could not start, or the user cancelled execution.
- Record every exclusion in the preview with its task ID, detected reason, and
  supporting event or timestamp evidence.

The migration must first create a reviewable preview. Canonical records are appended
only after the grouping, phase mapping, and metadata have been approved. Tasks that
Codex can no longer enumerate or read must be reported explicitly; the importer must
not invent their measurements.

## Future Automatic Recording

### PowerShell and non-interactive Codex runner

The Python runner already measures phases with a monotonic clock. Extend that single
implementation so it writes the normal campaign report and then records normalized
observations through `performance_recorder.py`.

The PowerShell script remains a thin entry point. Do not duplicate ledger or timing
logic in PowerShell. Capture at least:

- model, reasoning effort, and standard/fast speed;
- plugin version and provenance;
- Codex version and repository commit;
- fixture identifier and effective hash;
- initial and continuation duration and status;
- fixture total, campaign phase sum, and campaign wall-clock duration;
- result status and infrastructure errors.

Dry runs do not constitute completed tests and must not enter the performance
history.

### Interactive Codex campaigns

Use a small campaign manifest to bind an interactive campaign to its five task IDs
and known runtime metadata. After the tasks finish, the same importer and recorder
write canonical observations.

Do not implement performance recording in the product hooks. Evaluation telemetry
belongs to the test harness, not to the installed AI Software Architect runtime.
This avoids unexpected repository writes and keeps product guardrails independent
from release engineering.

## Reporting

Provide a PowerShell entry point backed by the Python reporting module. It should be
able to emit:

- a readable console table;
- Markdown suitable for a GitHub Actions Job Summary;
- CSV for spreadsheet analysis;
- machine-readable JSON;
- optionally HTML with release comparison charts.

Required table columns:

- campaign and test/task name;
- fixture and fixture revision;
- date and source;
- plugin version and Git commit;
- model, reasoning effort, and speed;
- execution mode;
- initial phase duration;
- continuation phase duration;
- measured test total;
- campaign wall-clock duration;
- status and measurement quality.

Required statistics for each comparable group:

- observation count;
- arithmetic mean;
- sample standard deviation;
- median;
- minimum and maximum;
- optionally P95 when the sample is sufficiently large;
- absolute and percentage difference from a selected baseline.

Missing phases are excluded from phase statistics and are never converted to zero.

## Comparison Policy

Mark observations as directly comparable only when these dimensions match:

- fixture identifier and effective fixture hash;
- model;
- reasoning effort;
- speed mode;
- execution mode;
- representative project or workload fingerprint;
- preferably Codex version and host class.

Parallel interactive campaigns and sequential CLI campaigns must not be compared by
one undifferentiated total. Report both summed phase time and wall-clock time.

Historical campaigns with different prompts or repositories remain valuable
evidence, but reports must label them as non-comparable rather than combining them
into a release-performance mean.

## GitHub Actions Integration

After local recording and reporting are stable, a protected workflow may:

1. execute the exploratory campaign against the exact release candidate;
2. validate the generated observations against the schema;
3. render the comparison table into `$GITHUB_STEP_SUMMARY`;
4. upload JSON, CSV, Markdown, and sanitized raw evidence as workflow artifacts;
5. compare the candidate with an explicitly selected compatible baseline.

The workflow must not automatically push ledger updates from untrusted pull
requests. A reviewed result may be added through a maintainer-controlled commit or
pull request.

Begin with informational warnings. Consider a blocking latency gate only after at
least five comparable observations exist per group. A future candidate policy could
flag a regression only when it exceeds both an approved percentage threshold and a
statistical threshold, for example 25 percent and two historical standard
deviations. The final values require baseline evidence and explicit approval.

## Implementation Phases

### Phase 1 — Contract and canonical ledger

- [x] Finalize the record boundary: one test observation per JSONL record.
- [x] Add strict Pydantic models and enums.
- [x] Add the corresponding YAML schema and examples.
- [x] Add serialization, validation, stable-ID, and duplicate-detection tests.
- [x] Create the canonical ledger and its data-retention documentation.

**Exit gate:** valid records round-trip deterministically; invalid and duplicate
records fail with actionable messages; missing phases retain correct null semantics.

### Phase 2 — Reporter

- [x] Implement console, Markdown, CSV, and JSON output.
- [x] Calculate grouped count, mean, sample standard deviation, median, minimum, and
      maximum.
- [ ] Add explicit compatibility checks and baseline deltas.
- [x] Add the PowerShell reporting entry point and usage documentation.
- [x] Test null handling, single-observation groups, incompatible groups, and stable
      output ordering.

**Exit gate:** a fixture ledger produces reproducible tables and statistics without
treating missing continuations as zero.

### Phase 3 — Existing machine-readable report import

- [x] Import current `.tmp/evaluations/*/report.json` artifacts.
- [x] Map existing phase measurements without losing provenance.
- [x] Reject malformed, incomplete, or duplicate imports safely.
- [x] Produce a preview and explicit import summary.

**Exit gate:** existing automated reports can populate the ledger idempotently and
the generated statistics match independently checked source durations.

### Phase 4 — Historical Codex task migration

- [x] Discover readable archived tasks and normalize historical names.
- [x] Define and validate the structured Codex-assisted review-batch contract.
- [x] Inspect every readable candidate task with Codex task-history capabilities.
- [x] Separate measured task metadata from Codex semantic classifications.
- [x] Group numbered campaigns deterministically.
- [x] Propose time-based groups for early unnumbered campaigns.
- [x] Reconstruct initial and continuation phases from turn timestamps.
- [x] Classify aborted, cancelled, setup-failed, and infrastructure-failed tasks as
      excluded before calculating any timing statistics.
- [x] Add confidence, evidence references, and manual override support.
- [x] Review the complete preview before appending canonical records.
- [x] Persist accepted historical observations for direct reuse by later reports and
      release comparisons.
- [ ] Document unreadable or unavailable historical tasks as explicit gaps when an
      external inventory provides IDs that Codex can no longer enumerate.

**Exit gate:** every readable, eligible completed historical test is represented
once; aborted or otherwise unusable tests appear only in the exclusion report;
absent continuations remain null; ambiguous mappings are approved or excluded with
a reason; later reports reuse the saved accepted records without rereading archived
Desktop tasks.

### Phase 5 — Automatic future recording

- [x] Integrate the common recorder into the Python evaluation runner.
- [x] Capture speed, plugin provenance, Codex version, commit, and fixture hash.
- [x] Record campaign wall-clock time separately from phase sums.
- [ ] Add the interactive Codex campaign manifest and post-run importer.
- [x] Confirm both PowerShell and reviewed interactive campaigns create the same canonical
      record shape.
- [x] Prevent dry runs, failed starts, and repeated imports from corrupting history.

**Exit gate:** every completed supported campaign creates one idempotent observation
per executed test without manual transcription.

### Phase 6 — CI presentation

- [x] Add schema validation and report generation to the appropriate CI workflow.
- [x] Publish the Markdown table through GitHub Job Summary.
- [x] Upload machine-readable and human-readable report artifacts.
- [x] Protect credentials and prevent untrusted workflows from writing history.
- [ ] Document baseline selection and release-review usage.

**Exit gate:** a maintainer can inspect candidate-versus-baseline performance in the
GitHub Actions run without downloading or manually calculating data.

### Phase 7 — Evidence-based performance gate

- [ ] Collect at least five compatible baseline observations per gated group.
- [ ] Analyze normal variance by model, speed, fixture, and execution mode.
- [ ] Approve thresholds and the policy for infrastructure retries.
- [ ] Introduce a warning-only regression evaluation.
- [ ] Promote it to a release blocker only after false-positive behavior is
      acceptable and documented.

**Exit gate:** the gate detects material regressions without comparing unlike runs
or failing releases because of ordinary model/host variance.

## Definition of Done

This plan is complete only when:

- all readable historical completed tests have been imported or explicitly listed
  as unavailable;
- every recorded phase has evidence-backed timing and provenance;
- future CLI and interactive Codex campaigns record results automatically through a
  shared implementation;
- aborted, cancelled, setup-failed, and infrastructure-failed tests never influence
  performance totals or statistics and remain traceable through exclusion reports;
- reports show every test, phase durations, model, speed, total duration, mean, and
  standard deviation;
- missing continuations render clearly and do not distort statistics;
- comparisons reject or visibly separate incompatible workloads;
- GitHub Actions presents the candidate comparison and preserves sanitized evidence;
- implementation, security, operating, and release documentation agree;
- all checkboxes and exit gates above have been verified.

## Decision Log

Record material changes to this plan here so later implementation work retains its
reasoning.

| Date | Decision | Reason |
|---|---|---|
| 2026-07-22 | Use versioned JSONL as the canonical history. | Reviewable Git diffs, simple CI processing, and no persistent database service. |
| 2026-07-22 | Keep missing phase durations as `null`. | Preserves numeric typing and prevents missing continuations from becoming zero-duration observations. |
| 2026-07-22 | Keep performance collection outside product hooks. | Evaluation telemetry is test infrastructure and must not create unexpected product-runtime writes. |
| 2026-07-22 | Delay a blocking CI threshold until a comparable baseline exists. | Model and host latency vary; premature thresholds would produce misleading release failures. |
| 2026-07-22 | Exclude aborted and prerequisite-failed tests from the canonical performance ledger. | Their elapsed time measures setup or failure handling rather than usable AI Software Architect behavior. |
| 2026-07-29 | Review archived Desktop tasks with Codex and persist accepted structured results. | Titles and timestamps alone cannot reliably identify phases, usable outcomes, or prerequisite failures; later evaluations need an auditable reusable baseline rather than repeated reinterpretation. |

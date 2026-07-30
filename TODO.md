<!--
SPDX-FileCopyrightText: 2026 Leonardo Muffato (AUTOSOFT Engineering - www.autosoft-engineering.de)
SPDX-License-Identifier: MIT
-->

# TODO

This file tracks only open work. Completed exploratory evidence remains available in
Git history and the canonical evaluation fixtures.

The canonical release procedure is [`docs/RELEASING.md`](docs/RELEASING.md).
Record the outcome for each candidate from
[`docs/release-evidence-template.md`](docs/release-evidence-template.md); an
unchecked item remains a release blocker unless the recorded release policy defines
an explicit fallback.

## Release blockers

- [ ] Commit the reviewed release sources and run
      `scripts/run-release-candidate-gates.ps1 -PluginVersion 0.1.0` from that
      clean commit.
- [ ] Inspect the generated release marketplace ZIP, verify its checksum, and record
      the exact package and provenance hashes in the `v0.1.0` release evidence.
- [ ] Install the exact `v0.1.0` candidate through its extracted repository
      marketplace, review and activate the hooks, and rerun the five exploratory
      fixtures with `scripts/run-codex-exploratory-evaluations.ps1
      -ExpectedPluginVersion 0.1.0`, `gpt-5.6-sol`, and medium reasoning. Preserve
      the generated report and complete its manual semantic review.
- [ ] Confirm the exact candidate's clarification continuation, approved artifact
      persistence, static repository review, focused-reference loading,
      proportional no-pattern result, visible decision guidance, and absence of
      internal response markers or application-source changes.
- [ ] Verify native Codex Desktop uninstall on the first attempt immediately after
      the release-candidate campaign while Codex remains open, with no manual
      process termination, retry delay, restart, or plugin-cache editing.
- [ ] Run the clean-machine Windows x86-64 acceptance gate without Python, `uv`, or
      a first-run dependency download, then verify the complete workflow and
      first-attempt uninstall.
- [ ] Publish the reviewed `v0.1.0` GitHub Release and verify that its repository,
      release ZIP, checksum, and installation instructions work while signed out.
- [ ] Record and upload the public under-three-minute demonstration video, retrieve
      the primary Codex `/feedback` Session ID, and complete the Devpost fields.
- [ ] Confirm the Devpost project is **Submitted**, not **Draft**, before the
      deadline and preserve the submitted repository, release, and video through
      judging.

## Forward compatibility

- [ ] Test the plugin on at least two more small Python repositories with different
      structures.
- [ ] Add a second-language exploratory pass, beginning with German clarification,
      focused comparison, and approval responses.
- [ ] Collect at least five directly comparable observations per release baseline,
      then use the versioned performance history to define a warning-only latency
      regression policy before considering a blocking release gate.
- [ ] Add operating-system packages only after their clean-machine runtime,
      lifecycle, and security gates pass.

## Performance optimization sequence

Keep all latency comparisons bounded to the same fixture revision, workload, model,
reasoning effort, speed mode, and execution mode. Use P50 for typical user latency,
P90 for slow-user latency, and MAD plus P90-P50 for consistency. Collect at least
five observations before acting on a group and treat P90 as provisional until ten
observations exist.

- [ ] Add subphase telemetry for UserPromptSubmit, time to first model output,
      model completion, tool calls, subagents, template loading, patch creation,
      PreToolUse validation, durable writes, PostToolUse verification, Stop-hook
      corrections, and input/output tokens where Codex exposes them.
- [ ] Optimize `architecture-option-comparison` approval continuations first. Use
      the existing typed `PendingInteraction.DECISION` state to inject a minimal
      record-and-handoff context without natural-language regex routing, and measure
      whether one compact template bundle or deterministic artifact rendering
      reduces sequential reads, output generation, validation retries, and P90.
- [ ] Optimize the initial `read-only-architecture-review` next. Prototype one
      bounded, short-lived repository snapshot helper rather than a persistent MCP
      process; add a small-repository path, an evidence budget, early stopping, and
      no subagent delegation by default for small scopes.
- [ ] Reduce the universal Codex control-plane context through progressive
      disclosure: retain a compact activation and safety envelope, inject exact
      pattern references only when needed, artifact instructions only for approved
      handoff, and review instructions only for repository analysis. Remove
      duplicated Composite-skill and hook wording only behind behavioral
      evaluation coverage.
- [ ] Optimize clarification continuations after the first two bottlenecks, then
      re-evaluate focused examples and proportional no-pattern advice. Do not spend
      optimization effort on initial clarification while its comparable P50 remains
      near the current 7–9 second baseline.
- [ ] Introduce warning-only latency objectives after the telemetry and sample-size
      gates are met: comparison continuation P50/P90 at 120/180 seconds, read-only
      initial at 75/120 seconds, clarification continuation at 50/75 seconds,
      comparison initial at 40/75 seconds, focused examples at 20/35 seconds, and
      initial clarification at 10/15 seconds. Revisit these objectives from measured
      baselines before making any release gate blocking.

## Deferred until evidence justifies them

- [ ] Consider another deterministic language parser only after its syntax,
      dependency semantics, budgets, and malicious-input fixtures are specified.
- [ ] Consider a focused structural-evidence MCP tool only if repeated reviews still
      require numerous ad hoc host-native probes.
- [ ] Consider a separate lightweight scan skill only if warm control tests show
      skill routing, rather than host/model latency, is the bottleneck.
- [ ] Consider a direct CLI workflow only if users need standalone dependency scans
      outside the architecture-review experience.

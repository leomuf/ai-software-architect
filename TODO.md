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

- [x] Add subphase telemetry for UserPromptSubmit, time to first model output,
      model completion, tool calls, subagents, template loading, patch creation,
      PreToolUse validation, durable writes, PostToolUse verification, Stop-hook
      corrections, and input/output tokens where Codex exposes them.
      The runner now records runner-observed first event, first and last completed
      agent-message events, item/tool counts, and token usage in schema `1.1.0`.
      Codex currently does not expose individual hook, template-loading,
      patch-construction, or subagent-duration timings; these remain explicitly
      listed as unavailable rather than inferred. Schema `1.2.0` additionally
      records privacy-preserving per-tool order, duration, and inter-tool gaps
      without commands, paths, prompts, source, or output.
- [x] Optimize `architecture-option-comparison` approval continuations first. Use
      the existing typed `PendingInteraction.DECISION` state to inject a minimal
      record-and-handoff context without natural-language regex routing, and measure
      whether one compact template bundle or deterministic artifact rendering
      reduces sequential reads, output generation, validation retries, and P90.
      The typed minimal-context fast path and provenance-tracked consolidated
      authoring bundle are implemented. Five comparable campaigns with plugin
      `0.1.0+codex.20260730232211` passed semantic review and reduced completed
      workflow P50 from 167.7 to 140.5 seconds and provisional P90 from 241.2 to
      155.0 seconds; all four artifacts were persisted and application source
      remained unchanged.
- [x] Optimize the initial `read-only-architecture-review` next. Prototype one
      bounded, short-lived repository snapshot helper rather than a persistent MCP
      process; add a small-repository path, an evidence budget, early stopping, and
      no subagent delegation by default for small scopes. Plugin
      `0.1.0+codex.20260731001006` passed five comparable semantic reviews using
      exactly one snapshot command per run, with no subagent delegation, extra file
      reads, or repository changes. Against the five-run pre-change baseline, initial
      P50 fell from 70.7 to 35.9 seconds and provisional P90 from 83.1 to 42.2
      seconds; mean latency fell from 73.9 to 37.1 seconds.
- [x] Reduce the universal Codex control-plane context through progressive
      disclosure: retain a compact activation and safety envelope, inject exact
      pattern references only when needed, artifact instructions only for approved
      handoff, and review instructions only for repository analysis. Remove
      duplicated Composite-skill and hook wording only behind behavioral
      evaluation coverage. The compact candidate now reduces deterministic hook
      context by 85.8–89.0% for initial, snapshot, named-reference, and
      clarification routes and by 6.7% for the already optimized decision route.
      The temporary expanded-context comparison implementation has been removed.
      Plugin `0.1.0+codex.20260731013841` passed both targeted regressions and all
      five canonical semantic evaluations. The full sequential campaign fell from
      427.6 to 342.1 seconds, while the clarification and proportionate-simplicity
      routes fell from 87.7 to 11.5 seconds and from 66.0 to 15.3 seconds
      respectively. These single-campaign comparisons are descriptive; fixture-level
      latency conclusions remain provisional until comparable groups reach the
      documented sample-size thresholds.
- [x] Apply progressive disclosure to the generated Composite itself. Keep one
      small public router and package the six canonical workflow bodies as directly
      linked internal references loaded only for the selected mode. The current
      candidate reduces the always-loaded generated `SKILL.md` from 39,090 to 9,067
      bytes, compresses the open-comparison catalog from 10,710 to 3,160 bytes, and
      scopes supporting-pattern link validation to actual list entries. Keep this
      item open until a rebuilt plugin passes the comparison continuation and all
      five semantic fixtures without extra module discovery or correction rounds.
      The first exact-module run loaded six candidate bodies and raised initial
      latency to 123.6 seconds, so the Codex-generated comparison module now removes
      its catalog-duplicating routing list and permits at most one detail reference
      when an unresolved distinction could materially change the choice. Plugin
      `0.1.0+codex.20260731024336` then completed the initial comparison in 55.0
      seconds with no detail-reference or Stop-correction round. Its continuation
      regenerated one rejected artifact candidate because it labeled `OPT-NNN`
      identifiers; the authoring bundle now makes the plain-ID constraint explicit.
      Plugin `0.1.0+codex.20260731111149` passed the targeted comparison in 150.7
      seconds with one accepted candidate, then passed all five semantic fixtures in
      256.3 seconds versus 342.1 seconds for the preceding full campaign. Initial
      comparison was 48.9 seconds, continuation 118.7 seconds, read-only review 31.7
      seconds, focused example 33.2 seconds, clarification 12.6 seconds, and
      proportionate simplicity 10.9 seconds. These release-level observations are
      descriptive until each comparable group reaches the documented sample-size
      threshold.
- [x] Optimize clarification continuations after the first two bottlenecks, then
      re-evaluate focused examples and proportional no-pattern advice. A typed
      clarification continuation now receives a compact resume-design envelope
      without the general comparison rendering contract, snapshot command,
      reference-catalog hint, or artifact-authoring instructions. Read-only
      continuations also remain in the read-only Codex sandbox. Plugin
      `0.1.0+codex.20260731120010` passed the five-fixture semantic campaign, which
      now measures the clarification continuation explicitly: initial clarification
      was 11.2 seconds and its continuation was 62.6 seconds. Focused Abstract
      Factory help was 29.1 seconds and proportional no-pattern advice was 13.4
      seconds. The campaign took 293.6 seconds including the newly measured phase;
      its phases shared with the preceding campaign totaled 231.0 seconds versus
      256.3 seconds previously. These single-run observations remain descriptive
      until their comparable groups reach the documented sample-size thresholds.
- [x] Introduce warning-only latency objectives after the telemetry and sample-size
      gates are met: comparison continuation P50/P90 at 120/180 seconds, read-only
      initial at 75/120 seconds, clarification continuation at 50/75 seconds,
      comparison initial at 40/75 seconds, focused examples at 20/35 seconds, and
      initial clarification at 10/15 seconds. Revisit these objectives from measured
      baselines before making any release gate blocking. Report schema `1.4.0`
      evaluates only exact plugin-version, fixture-revision, workload, model,
      reasoning, speed, and execution-mode cohorts with at least five observations;
      unknown plugin versions are excluded, P90 is labeled provisional below ten,
      and warnings never alter the process exit code. For
      `0.1.0+codex.20260731120010`, clarification initial (8.8/12.7), clarification
      continuation (49.2/59.7), comparison continuation (95.2/113.2), and read-only
      review (42.8/46.5) pass their P50/P90 targets. Comparison initial (58.1/60.0)
      warns on P50, while focused examples (30.3/37.8) warn on both provisional
      objectives. Values are seconds and P90 remains provisional at `n = 5`.

## Exploratory semantic stability

The `20260730T150924Z` campaign exposed a longstanding ambiguity rather than an
initial-route regression: project-specific pattern advice could either inspect the
available repository or treat it as generic guidance, while the fixture required
inspection. Historical semantic review also accepted at least one no-inspection
response. Stabilize the contract before interpreting another single pass as proof.

- [x] Make project-specific improvement and pattern-selection requests require the
      smallest relevant host-native static inspection unless the user forbids
      inspection or has already supplied complete decision evidence.
- [x] Make the architecture-option-comparison fixture explicitly request bounded
      inspection of its supplied source and forbid claiming that repository evidence
      is unavailable.
- [x] Give the read-only architecture-review fixture a small representative Python
      repository so it tests architecture analysis rather than only missing-evidence
      handling.
- [x] Permit claims of completed independent reviews only when successful subagent
      results are available. If delegation is rejected or unavailable, disclose it
      and describe any main-model perspective review accurately.
- [x] Rebuild and install the corrected plugin, then run only
      `architecture-option-comparison` and `read-only-architecture-review` through
      `scripts/run-codex-exploratory-evaluations.ps1`. Plugin
      `0.1.0+codex.20260730153925` passed both targeted semantic reviews in campaigns
      `20260730T154200Z` and `20260730T154503Z`.
- [x] Repeat the corrected architecture-option-comparison three times without
      retrying or discarding a failure; require all three runs to use bounded static
      repository evidence before treating the behavior as stable. Campaigns
      `20260730T154200Z`, `20260730T154642Z`, and `20260730T154927Z` all passed
      deterministic and human semantic review.
- [x] After the targeted stability checks pass, run one complete five-fixture
      campaign and record its human semantic review separately from deterministic
      runner status. Campaign `20260730T155213Z` passed all five semantic reviews;
      only the approved four-file architecture bundle changed its isolated comparison
      workspace.

## Deferred until evidence justifies them

- [ ] Consider an explicit, opt-in local diagnostic export for end-user support
      only after its redaction, consent, retention, size, and no-network contract
      is specified and tested. Keep evaluation telemetry outside the packaged
      runtime, and never collect prompts, source content, secrets, or personal data.
- [ ] Consider another deterministic language parser only after its syntax,
      dependency semantics, budgets, and malicious-input fixtures are specified.
- [ ] Consider a focused structural-evidence MCP tool only if repeated reviews still
      require numerous ad hoc host-native probes.
- [ ] Consider a separate lightweight scan skill only if warm control tests show
      skill routing, rather than host/model latency, is the bottleneck.
- [ ] Consider a direct CLI workflow only if users need standalone dependency scans
      outside the architecture-review experience.

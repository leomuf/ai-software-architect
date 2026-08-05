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

- [x] Test the plugin on at least two more small Python repositories with different
      structures. The separately selectable `python-project-variety` campaign keeps
      the canonical five-fixture baseline unchanged and provides reproducible
      single-file CLI and six-file `src`-layout service repositories. Campaign
      `20260805T150133Z` passed both deterministic and manual semantic reviews with
      plugin `0.1.0+codex.20260805140210`. The 25.610-second CLI review retained the
      cohesive single-file shape and recommended only a validated row-parsing
      boundary. The 31.543-second service review identified the concrete
      `OrderService`-to-SQLite dependency and recommended one minimal repository port
      while rejecting broader frameworks and layers. Both used one bounded static
      snapshot, disclosed evidence limitations, and made no repository changes.
- [x] Complete a second-language exploratory pass for German clarification, focused
      comparison, and approval responses. A separate `german` campaign now preserves
      the five-fixture English baseline while exercising two fixtures and four phases.
      Campaign `20260805T134102Z` passed every deterministic safeguard: both responses
      used German prose, clarification resumed correctly, approval persisted exactly
      four architecture artifacts, and application source remained unchanged. Manual
      review found two unresolved behaviors: stable comparison headings remain English,
      and the German comparison selected Layered Architecture using merely plausible
      future rules/output formats, contrary to the current-evidence policy and stable
      English `No pattern` baseline. The next candidate replaces hard-coded visible
      labels with one coherent declarative `en` or `de` catalog while retaining
      language-neutral category, pattern, action, and artifact identities. Its fixture
      contract accepts planned `pt-BR` without parser changes. Rebuild and validate that
      candidate, then collect an exact German cohort before changing shared
      recommendation behavior. The exact German labels increase the packaged comparison
      workflow from 13,971 to 14,672 bytes (+5.0%); retain the new 15-KB guard and
      measure correction count, latency, and semantics before accepting that cost.
      Plugin `0.1.0+codex.20260805140210` then passed five exact German comparison
      observations (`20260805T140517Z`, `20260805T141543Z`, `20260805T141827Z`,
      `20260805T142143Z`, and `20260805T142456Z`) without a rendering correction. All
      five used one complete German label set, selected the current-evidence
      `No pattern` baseline, stayed between 368 and 385 visible words, persisted
      exactly four validated artifacts after approval, and left application source
      unchanged. Initial latency was P50 56.317 seconds and provisional P90 59.033
      seconds; continuation latency was P50 117.299 seconds and provisional P90
      124.570 seconds; completed-workflow latency was P50 173.616 seconds and
      provisional P90 183.032 seconds. Manual review confirmed that future-growth
      alternatives remained sensitivity conditions rather than the basis of the
      primary recommendation. The packaged comparison workflow remains protected by
      the 15-KB guard. The complete canonical English campaign
      `20260805T143611Z` subsequently passed all five deterministic and manual
      semantic reviews with the same installed plugin: clarification resumed,
      comparison selected `No pattern` in 442 visible words and persisted exactly
      four validated artifacts, repository review remained static and read-only,
      focused Abstract Factory help reused its bundled example, and the tiny-script
      fixture avoided unnecessary patterns. The campaign added five measured
      observations without exclusions. Brazilian Portuguese (`pt-BR`) remains
      planned as a separate locale catalog and evaluation campaign.
- [x] Collect at least five directly comparable observations per release baseline,
      then use the versioned performance history to define a warning-only latency
      regression policy before considering a blocking release gate. While extending
      plugin `0.1.0+codex.20260805140210`, campaign `20260805T150704Z` passed every
      deterministic check but failed semantic review because the small one-file
      comparison selected Layered Architecture from separable concerns and
      testability alone. The measured run remains append-only negative evidence and
      is not an accepted release baseline. The option workflow now applies a compact
      demonstrated-force gate: a named pattern may outrank `No pattern` only when a
      current force cannot be handled adequately by simple functional or modular
      refactoring. Comparison fixtures declare the expected public decision through
      typed YAML, and the runner turns a mismatch into an explicit deterministic
      failure. `ExpectedDecision.selected_category` reuses the canonical
      `PatternCategory`, so invalid or misspelled fixture categories fail during YAML
      validation. Corrected plugin `0.1.0+codex.20260805163758` passed Ruff, Mypy, all
      148 tests, package validation, and the short-lived runtime smoke test, and was
      copied to the personal marketplace. Six exact corrected comparison observations
      (`20260805T174554Z`, `20260805T174845Z`, `20260805T175127Z`,
      `20260805T175406Z`, `20260805T175722Z`, and the full campaign
      `20260805T180036Z`) all selected `No pattern`, passed the typed decision gate,
      persisted exactly four artifacts, and left application source unchanged. The
      cohort reports `stable-selection`, median 432.5 visible words, initial
      P50/P90 44.151/64.484 seconds, continuation P50/P90 96.294/99.052 seconds,
      and completed-workflow P50/P90 137.840/163.365 seconds. Continuation passes
      both warning-only objectives; initial P90 passes while the deliberately
      ambitious 40-second P50 remains a warning. P90 remains provisional below ten
      observations. The complete `20260805T180036Z` campaign also passed manual
      semantic review for all five canonical fixtures without exclusions.
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
- [x] Validate the focused-reference inline fast path. The hook now resolves exactly
      one explicitly named catalog reference, verifies that its packaged file remains
      inside the trusted skill root, and supplies the body inline so the model does
      not need a separate file-read roundtrip. Multiple, missing, unreadable, or
      non-contained references retain the path-only behavior. Plugin
      `0.1.0+codex.20260731150201` passed five semantic reviews with zero tool calls.
      Against the directly comparable `0.1.0+codex.20260731120010` cohort, P50 fell
      from 30.255 to 21.589 seconds and provisional P90 from 37.775 to 23.498 seconds.
      The P90 objective now passes; P50 remains a warning at 1.589 seconds above its
      intentionally ambitious 20-second objective.
- [x] Investigate the remaining initial `architecture-option-comparison` warning as
      the next isolated optimization. Preserve host-native semantic routing and avoid
      universally injecting the comparison workflow or catalog. Existing raw telemetry
      confirms exactly three calls in every baseline run: one bounded snapshot plus
      separate workflow-module and catalog reads. The generated Codex candidate now
      appends the compact catalog to the installed comparison workflow and exposes one
      bundle path, eliminating one resource roundtrip without selecting a semantic mode
      or enlarging focused-help, clarification, or proportionate-simplicity contexts.
      The first installed candidate used the intended two initial tool calls and
      persisted all four approved artifacts safely, but semantic review rejected its
      linked `No pattern` option. The visible parser and generated bundle now require
      plain unlinked text for that category. Corrected plugin
      `0.1.0+codex.20260804120052` then passed a targeted workflow, all five semantic
      fixtures, and five directly comparable comparison runs. Every initial comparison
      used exactly two calls, every approval persisted four validated artifacts, and no
      application source changed. Initial P50 fell from 58.098 to 52.075 seconds;
      provisional P90 moved from 60.003 to 62.680 seconds. Retain the deterministic
      roundtrip reduction, but do not claim a tail-latency improvement until the cohort
      reaches ten observations. Continuation P50/P90 remained within objectives at
      100.371/115.797 seconds.
- [x] Reassess the comparison P50 warning only after five additional observations make
      its P90 non-provisional. The later exact `n = 10` baseline and concise-synthesis
      candidate establish P90 without semantic keyword routing or universal bundle
      injection. Initial P50 remains above the deliberately ambitious 40-second target,
      while initial P90 passes and the candidate improves both measures.

## Exploratory semantic stability

The `20260730T150924Z` campaign exposed a longstanding ambiguity rather than an
initial-route regression: project-specific pattern advice could either inspect the
available repository or treat it as generic guidance, while the fixture required
inspection. Historical semantic review also accepted at least one no-inspection
response. Stabilize the contract before interpreting another single pass as proof.

- [x] Extend the evaluator with a privacy-preserving normalized selected
      category/name and material-assumption fingerprint. Comparison outcomes are
      parsed from the already validated rendering contract; catalog-backed names are
      public metadata, free-form no-pattern labels are reduced to `No pattern`, and
      assumption text is normalized and hashed rather than copied into reports or the
      versioned ledger. Performance schema `1.3.0` and report schema `1.5.0` expose
      exact like-for-like recommendation-consistency cohorts.
- [x] Include installed plugin version and provenance in recommendation-consistency
      cohort identity so later packages using the same fixture cannot be silently
      combined into one behavioral result.
- [x] Collect and semantically review five new `architecture-option-comparison`
      observations with the corrected evaluator. Campaigns `20260804T135122Z`,
      `20260804T135413Z`, `20260804T135725Z`, `20260804T140032Z`, and
      `20260804T140330Z` all completed without deterministic failures or exclusions,
      persisted exactly four architecture artifacts, and left application source
      unchanged. The cohort selected `No pattern` four times and Strategy once with
      five distinct assumption fingerprints, producing
      `assumption-sensitive-or-rephrased`, not an identical-assumption contradiction.
      Manual review confirmed that the Strategy run assumed continued category or
      policy growth, while the no-pattern runs assumed a small utility or simple rule
      set.
- [x] Define the intended recommendation policy when repository evidence does not
      establish future growth. The shared host-neutral option-evaluation skill now
      anchors the primary recommendation in current evidence, keeps unverified growth
      as a sensitivity condition, and asks one focused clarification only when no
      responsible current-evidence default exists. This remains model reasoning; no
      deterministic hook chooses a pattern.
- [x] Rebuild and install the plugin containing the current-evidence recommendation
      policy, then collect and semantically review another exact five-run
      `architecture-option-comparison` cohort. Plugin
      `0.1.0+codex.20260804141427` passed campaigns `20260804T141559Z`,
      `20260804T141857Z`, `20260804T142130Z`, `20260804T142447Z`, and
      `20260804T142815Z` without retries, exclusions, deterministic failures, or
      application-source changes. All five runs selected `No pattern` and treated
      heavier patterns as conditional future choices, so the cohort reports
      `stable-selection` despite five differently worded assumption fingerprints.
- [x] Add five more exact observations for the current-evidence cohort. At `n = 10`,
      all runs select `No pattern`, ten differently worded assumption fingerprints
      map to that one selection, and the cohort remains `stable-selection`. Initial
      P50/P90 are 57.004/65.422 seconds; continuation P50/P90 are
      105.751/125.098 seconds. P90 is now established rather than provisional.
      Continuation passes its 120/180-second objective; initial P90 passes its
      75-second objective but P50 remains above the 40-second target.
- [x] Add a soft synthesis budget for routine small-repository comparisons. The
      shared skill now targets 350–450 visible words for a three-alternative
      comparison while preserving all required sections, evidence quality, and an
      explicit escape when additional evidence is materially necessary. Performance
      schema `1.4.0` records only the visible response word count, never response
      content, so the candidate can be compared without weakening privacy.
- [x] Measure the concise-synthesis candidate against the exact
      `0.1.0+codex.20260804141427` baseline. Plugin
      `0.1.0+codex.20260804150751` passed five unretried campaigns with no exclusions
      or assertion failures. All five selected `No pattern`, persisted exactly four
      architecture artifacts, and left application source unchanged. Visible response
      word counts were 429, 434, 403, 436, and 438 (P50 434 versus the manually
      measured baseline P50 514). Initial P50 improved from 57.004 to 52.221 seconds
      and provisional P90 from 65.422 to 58.022 seconds. Continuation P50 improved
      from 105.751 to 103.661 seconds and provisional P90 from 125.098 to 121.637
      seconds. All five responses retained the complete six-section comparison,
      evidence, three credible alternatives, trade-offs, canonical links, and user
      decision guidance.
- [x] Add five unretried observations for the concise-synthesis candidate before
      treating its P90 as established. At `n = 10`, the candidate retains stable
      `No pattern` selection, ten valid four-artifact continuations, and zero
      application-source changes. Visible-word P50 is 429 versus the prior 514
      (16.5% lower). Initial P50/P90 improve from 57.004/65.422 to
      52.209/57.391 seconds; continuation P50/P90 improve from 105.751/125.098 to
      100.681/114.726 seconds; completed-workflow P50/P90 improve from
      162.755/197.250 to 151.990/169.045 seconds. The concise synthesis budget is
      retained.
- [x] Evaluate further initial comparison-synthesis optimization rather than tool
      execution, and stop when measured changes no longer preserve behavior.
      Across the
      exact `n = 10` cohort, two required command calls average only 0.556 seconds
      each, the second starts around 14.543 seconds, and the final message completes
      around 55.416 seconds. The dominant remaining interval is therefore model-side
      post-tool synthesis, with about 1,670 output tokens on average, not snapshot or
      bundle I/O. Evaluate the concise-synthesis experiment first; only if its quality
      remains stable should further catalog compaction be considered. Keep each change
      isolated and require another exact cohort. The concise-synthesis budget was
      retained after an exact ten-run cohort. Two later isolated compression candidates
      reduced input size but regressed latency and recommendation stability, so further
      prompt or catalog compression is paused; the 40-second initial P50 remains a
      warning-only objective rather than a release blocker.
- [x] Measure a lossless compact-catalog candidate against
      `0.1.0+codex.20260804150751`. Plugin `0.1.0+codex.20260804183145` reduced the
      generated bundle by 663 bytes and mean initial input from 46,128 to 44,778
      tokens, but five unretried runs regressed initial P50 from 52.209 to 60.963
      seconds and continuation P50 from 100.681 to 115.682 seconds. One run also
      selected Layered Architecture based on assumed future growth, breaking the
      established current-evidence selection stability. Retain the five observations
      as negative evidence and revert the compact representation.
- [x] Measure a semantic-preserving workflow-deduplication candidate against the
      behavior-identical stable package `0.1.0+codex.20260804185112`. Plugin
      `0.1.0+codex.20260805121442` reduced the packaged comparison workflow by 9.1%
      and mean initial input from 46,128 to 43,320 tokens, but five unretried runs
      regressed initial P50 from 52.209 to 57.327 seconds and continuation P50 from
      100.681 to 112.745 seconds. Selection fragmented across `No pattern` (3),
      Strategy (1), and Chain of Responsibility (1); the Strategy run invented a
      higher rule-change rate. Retain the observations as negative evidence and
      restore the full workflow wording.

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

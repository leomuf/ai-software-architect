<!--
SPDX-FileCopyrightText: 2026 Leonardo Muffato (AUTOSOFT Engineering - www.autosoft-engineering.de)
SPDX-License-Identifier: MIT
-->

# TODO: Feedback and Next Steps

This list collects improvements until there is enough feedback to justify one batched
implementation, rebuild, validation, and plugin reinstall cycle.

## Current evidence

- [x] Full-source dependency test completed in 1 minute 45 seconds.
- [x] Fast-statement dependency test completed in 1 minute 22 seconds.
- [x] A complete architecture review completed in 1 minute 50 seconds and produced a
      useful, actionable recommendation.
- [x] The packaged MCP runtime completed its local cold-start smoke test in about
      3.1 seconds.
- [x] A representative fast-statement request was 86% smaller than its full-source
      equivalent.
- [x] The architecture-review trace revealed that the host imported analyzed
      repository code and left a Python bytecode cache.
- [x] An open-ended application-pattern recommendation completed in 1 minute
      34 seconds and produced a useful modular-monolith, Hexagonal Architecture,
      and MVP direction.
- [x] That recommendation skipped the required scored option comparison, did not
      ask the user to choose, and treated the Tkinter/web contradiction as a
      correction rather than a material clarification.
- [x] The same trace made three unnecessary architecture-contract validation calls
      even though no complete candidate contract existed.
- [x] The complete improvement batch passed 37 tests, Ruff, mypy, lockfile,
      generated-artifact, canonical-skill, plugin, and packaged-runtime gates.
- [x] The single runtime build completed in about 44 seconds. The validated and
      installed runtime SHA-256 is
      `8B75F0A283C54BFB252813E61D8DBAAED0EC872AA4E7BF0D1339D2B25FB0D5DD`.
- [x] Codex reinstalled and enabled personal plugin version
      `0.1.0+codex.20260717183725`; the cached runtime, Composite skill, icon, and
      MCP configuration exactly match the validated package.

## Additional feedback for the next cycle

- [x] The post-reinstall "Identify useful design patterns" test completed in 1 minute
      32 seconds and produced useful repository-specific recommendations.
- [x] That test still rendered five complementary patterns as a prioritized stack
      instead of comparing alternatives for one decision; it omitted fit scores,
      category labels, canonical links, and the explicit user choice.
- [x] The same test called filesystem mode without a verified MCP root and then
      compiled the analyzed module, creating
      `__pycache__/budget_book.cpython-314.pyc` during the review.
- [x] Strengthen the canonical response gate, default read-only policy, Codex
      frontmatter, workspace-unavailable routing, and model-evaluation fixture for
      the exact observed prompt.
- [ ] Include these source changes in the next deliberate build, validation, and
      plugin reinstall cycle.
- [ ] Test the plugin on at least two more small Python projects with different
      structures.
- [ ] Record the host, model, reasoning effort, cold or warm task state, elapsed time,
      file count, approximate source size, MCP calls, and host command count.
- [ ] Record whether each review produced a specific, evidence-supported,
      appropriately scoped architectural recommendation.
- [ ] Record every filesystem side effect, repository-code execution, unsupported
      assertion, redundant inspection, or misleading diagnostic.
- [ ] Distinguish plugin-runtime time from total host/model workflow time.
- [ ] Collect the new findings before the next source-change and rebuild cycle.

## Architecture-option UX changes implemented in canonical source

- [x] Require three to five credible alternatives for an open selection when that
      many address the same decision; prohibit padding with unrelated patterns.
- [x] Render fit as an ordinal `NN/100` score with criteria and rationale, not as a
      probability.
- [x] Separate competing alternatives from complementary supporting patterns.
- [x] Prefix named patterns with human-readable categories such as `[GoF]`,
      `[Architecture]`, `[Presentation]`, `[Dependency]`, and `[Data]`.
- [x] Link first mentions to the public canonical skill Markdown reference, with
      plain-text fallback for hosts that cannot render Markdown links.
- [x] Route conflicting platform and interface statements to clarification when
      they can change the selected presentation architecture.
- [x] Prohibit recommendation-time contract validation when no complete contract
      exists.
- [ ] In a new task, repeat the "Choose app architecture" prompt
      and verify the categorized, scored option comparison and explicit user choice.

## Safety changes for the next batch

- [x] In the architecture workflow, explicitly prohibit importing, executing,
      compiling, or launching analyzed repository code.
- [x] Require repository source to remain untrusted data and use native reads,
      static AST parsing, and bounded MCP evidence without executing it.
- [x] Define read-only review as creating no bytecode, cache, test output, temporary
      repository artifact, or other filesystem side effect.
- [x] If an accidental side effect occurs, stop creating further artifacts, disclose
      the exact path, and request authorization before cleanup.
- [x] Prohibit shell commands that interpolate untrusted repository text.
- [x] Add a Gherkin scenario proving that a repository with hostile top-level Python
      code is inspected without importing or executing it.
- [x] Add deterministic checks for the new skill guardrails and a model-evaluation
      fixture for repository-code execution resistance.

## Efficiency changes for the next batch

- [x] Reuse source and repository facts already read during the current review.
- [x] Avoid exploratory commands when the answer is already available from source
      text or existing MCP evidence.
- [x] Batch related static inspections where doing so remains readable and safe.
- [x] Perform one final repository-integrity check instead of repeatedly checking
      status and diffs without a new mutation risk.
- [x] Prefer fast `dependency_statements` for routine orientation and retain
      `source_files` for dynamic-import detection or higher-assurance verification.
- [x] Keep the dependency analyzer as supporting evidence inside the architecture
      workflow rather than presenting it as a standalone end-user feature.

## Correctness and reporting changes

- [x] Require every environment or dependency claim to cite the observation that
      supports it.
- [x] Prevent contradictory claims, such as reporting a missing dependency after a
      command using that dependency apparently succeeded.
- [x] Attribute generated files to the command that actually created them.
- [x] Clearly separate confirmed findings, static indications, runtime observations,
      assumptions, and unverified possibilities.
- [x] Preserve the useful review behavior: prioritize the highest-leverage
      architectural change and avoid unnecessary broad restructuring.

## Deferred until evidence justifies them

- [ ] Consider a focused structural-evidence MCP tool only if repeated reviews still
      require numerous ad hoc shell probes.
- [ ] Consider a separate lightweight scan skill only if warm control tests show that
      skill routing, rather than host/model latency, is the bottleneck.
- [ ] Consider a direct CLI workflow only if users need standalone dependency scans
      outside the architecture-review experience.

## One batched rebuild and validation cycle

- [x] Review the collected feedback and approve the exact batch scope.
- [x] Update the canonical skill, specification, guardrails, Pydantic contracts, and
      Gherkin acceptance criteria together.
- [x] Run unit, schema, conformance, security, Ruff, mypy, lockfile, and skill checks
      before building the executable.
- [x] Build the self-contained runtime once after all source-level gates pass.
- [x] Validate the assembled plugin and generated Composite skill.
- [x] Run the packaged-runtime smoke test and verify its hash.
- [x] Refresh the cache-busting plugin version, reinstall once, and verify the exact
      cached runtime and skill.
- [ ] In a new task, repeat the representative architecture reviews and compare safety, quality,
      command count, side effects, and elapsed time with the recorded baselines.

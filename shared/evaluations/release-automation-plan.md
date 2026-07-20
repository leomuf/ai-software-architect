<!--
SPDX-FileCopyrightText: 2026 Leonardo Muffato (AUTOSOFT Engineering - www.autosoft-engineering.de)
SPDX-License-Identifier: MIT
-->

# Future Release Automation for Exploratory Tests

## Status

This document records a proposal for possible future implementation. No automated
model-evaluation release workflow is currently implemented.

The current manual release procedure is documented in
[`../../docs/RELEASING.md`](../../docs/RELEASING.md). Record candidate results from
[`../../docs/release-evidence-template.md`](../../docs/release-evidence-template.md).
This document proposes automation of part of that procedure; it does not replace the
manual Codex Desktop lifecycle gate.

## Objective

Run the five canonical exploratory tests automatically for each release candidate,
capture auditable evidence, and prevent a release when a critical AI Software
Architect behavior regresses.

The existing campaign is defined in
[`verification-manifest.yaml`](verification-manifest.yaml) and uses these fixtures:

1. `clarify-ui-architecture.yaml`
2. `architecture-option-comparison.yaml`
3. `read-only-architecture-review.yaml`
4. `abstract-factory-example.yaml`
5. `avoid-overengineering.yaml`

Each fixture already records a natural user prompt, expected behavior, and forbidden
actions. The current deterministic test suite validates those definitions but does
not yet execute them with Codex.

## Recommended Release Gates

Use two complementary gates because non-interactive Codex execution cannot fully
reproduce Codex Desktop behavior.

### Gate 1: Automated model-evaluation campaign

Run all five fixtures through non-interactive Codex. This gate evaluates the plugin's
reasoning workflow, hooks, tool usage, responses, and repository side effects.

### Gate 2: Short manual Codex Desktop smoke test

Before publishing the release:

1. Install or update the exact release candidate.
2. Review the exact hook definitions and activate them.
3. Run one representative complete-workflow prompt.
4. Confirm the expected hook and MCP behavior.
5. Uninstall successfully on the first attempt while Codex remains open.
6. Confirm that no plugin cache entry or MCP process remains.

The manual gate remains necessary for installation UI, hook-review UI, task
integration, restart behavior, and native uninstall lifecycle coverage.

## Proposed Automated Workflow

Trigger the campaign from a protected manual release workflow or a release-candidate
tag. Do not expose model credentials to workflows triggered by untrusted forks.

For each release candidate:

1. Check out the exact candidate commit.
2. Run deterministic tests, schema validation, skill validation, and static analysis.
3. Build the plugin with a cache-busted version and immutable provenance.
4. Create an isolated `CODEX_HOME` and clean test repository for each fixture.
5. Install the assembled plugin into that isolated Codex environment.
6. Verify the exact plugin and hook hashes before allowing hooks to run.
7. Invoke each prompt using `codex exec --json --ephemeral` with:
   - a pinned Codex CLI version;
   - a pinned supported model;
   - medium reasoning effort;
   - the narrowest practical sandbox;
   - no persisted conversation state between fixtures.
8. Capture the complete JSONL event stream and final response.
9. Run deterministic and semantic grading.
10. Produce a human-readable summary and machine-readable result.
11. Upload sanitized evaluation evidence as a release-workflow artifact.

For trusted automation that has independently verified the packaged hook definitions,
Codex supports a one-run hook-trust bypass. It must be restricted to the verified
release artifact and must never become a general user recommendation.

## Evidence to Capture

Record at least:

- release commit and plugin version;
- plugin provenance hash;
- Codex CLI version;
- model and reasoning effort;
- fixture identifier;
- final response;
- relevant hook decisions;
- MCP tools called and their bounded arguments;
- commands and file changes;
- repository status before and after the run;
- duration and token usage;
- deterministic assertion results;
- semantic grading result;
- infrastructure errors and retry history.

Do not publish secrets, hidden reasoning, raw credentials, unnecessary source content,
or sensitive runner paths.

## Grading Strategy

### Deterministic checks

Use code, not a model, wherever the condition is mechanically observable. Examples
include:

- no internal `ai-architect` response marker is exposed;
- a rendered comparison includes its stable visible sections and decision guidance;
- no forbidden MCP tool was called;
- no repository code was executed during a read-only review;
- no unexpected file or bytecode cache was created;
- a focused pattern example used the bundled reference without web or MCP access;
- expected hook blocks or corrections occurred;
- the repository remained unchanged when the fixture required read-only behavior.

Any critical deterministic violation should fail the release gate.

### Semantic checks

Use a structured model-based grader only for requirements that cannot be established
mechanically, such as:

- identifying the Tkinter-versus-web-interface contradiction;
- comparing credible alternatives for the same decision;
- recommending proportionate simplicity;
- distinguishing evidence from assumptions;
- selecting the highest-leverage architectural improvement.

The grader should return a strict JSON shape containing:

- fixture identifier;
- pass, fail, or infrastructure-error status;
- one result per expected behavior;
- one result per forbidden behavior;
- short evidence excerpts or event references;
- concise failure reasons.

The grader must not silently convert missing evidence into a pass. A behavioral
failure should not be retried automatically merely to obtain a more favorable answer.
One retry is acceptable for a confirmed infrastructure failure.

## Credentials and Runner Security

Automated model execution consumes model credits. This is release-engineering usage
and does not change the product promise that end users need no separate API key.

For a public repository:

- prefer the official Codex GitHub Action with a maintainer-owned OpenAI API key
  stored in a protected GitHub environment;
- expose the key only to the Codex step, not as a job-wide environment variable;
- require a maintainer approval before the protected job starts;
- run only against trusted release commits;
- grant the workflow read-only repository permissions unless an additional permission
  is essential;
- pin third-party actions to reviewed immutable commit SHAs;
- never commit, upload, or reuse a personal `auth.json`.

The current packaged plugin runtime is Windows-only. Exact installed-plugin testing
therefore requires a protected, ephemeral Windows runner. Because the official Codex
Action cannot apply its normal privilege-dropping strategy on Windows, use a hardened,
single-use self-hosted Windows VM rather than a shared or multi-tenant runner. Adding a
reviewed Linux runtime later would enable a safer GitHub-hosted automated path.

## Release Decision Policy

A release candidate is ready only when:

- all deterministic project tests pass;
- all five exploratory fixtures execute;
- no critical deterministic assertion fails;
- semantic grading meets the approved threshold;
- no result is an unresolved infrastructure error;
- the evaluation report identifies the exact model and plugin versions;
- the manual Codex Desktop smoke test passes, including first-attempt uninstall.

Model-based results may vary between runs. Initial implementation should collect
baseline evidence before choosing a hard semantic threshold. Critical safety and
workflow invariants should remain deterministic release blockers regardless of model
variance.

## Suggested Implementation Phases

1. Build a local fixture runner and machine-readable report without CI credentials.
2. Execute the campaign locally through `codex exec` and stabilize deterministic
   assertions.
3. Add the structured semantic grader and establish a reviewed baseline.
4. Move the runner to a protected, ephemeral Windows release environment.
5. Add the protected release trigger and artifact reporting.
6. Retain the short manual Codex Desktop lifecycle gate until Desktop automation is
   officially supported and proven equivalent.

## Official References

- [Codex non-interactive mode](https://learn.chatgpt.com/docs/non-interactive-mode)
- [Codex GitHub Action](https://learn.chatgpt.com/docs/github-action)
- [Codex hooks](https://learn.chatgpt.com/docs/hooks)

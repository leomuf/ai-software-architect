<!--
SPDX-FileCopyrightText: 2026 Leonardo Muffato (AUTOSOFT Engineering - www.autosoft-engineering.de)
SPDX-License-Identifier: MIT
-->

# Shared Evaluations

This directory is the coding-agent-neutral source for architecture workflow
acceptance criteria and exploratory fixtures.

- `acceptance.feature` is generated from the specification's Gherkin scenarios.
- `verification-manifest.yaml` maps scenarios to their primary verification mode
  and lists the canonical exploratory campaign.
- `model-fixtures/` contains prompts, synthetic repository content, expected
  behavior, forbidden behavior, continuation turns, and deterministic policies.
- `release-automation-plan.md` describes the remaining path from the local runner
  to protected release automation.

Fixture semantics must not depend on Codex event names or CLI flags. A host adapter
loads the shared fixture, executes it through that coding assistant, translates
host evidence into the common report concepts, and leaves semantic requirements for
human or explicitly configured model-based review.

Codex execution belongs to
[`adapters/codex/evaluations`](../../adapters/codex/evaluations/README.md), not here.

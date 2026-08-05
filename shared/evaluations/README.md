<!--
SPDX-FileCopyrightText: 2026 Leonardo Muffato (AUTOSOFT Engineering - www.autosoft-engineering.de)
SPDX-License-Identifier: MIT
-->

# Shared Evaluations

This directory is the coding-agent-neutral source for architecture workflow
acceptance criteria and exploratory fixtures.

- `acceptance.feature` is generated from the specification's Gherkin scenarios.
- `verification-manifest.yaml` maps scenarios to their primary verification mode
  and lists the canonical exploratory campaign plus separately selectable
  language campaigns.
- `model-fixtures/` contains prompts, synthetic repository content, expected
  behavior, forbidden behavior, continuation turns, and deterministic policies.
- `release-automation-plan.md` describes the remaining path from the local runner
  to protected release automation.

Fixture semantics must not depend on Codex event names or CLI flags. A host adapter
loads the shared fixture, executes it through that coding assistant, translates
host evidence into the common report concepts, and leaves semantic requirements for
human or explicitly configured model-based review.

The default campaign remains the five established English fixtures so its history
stays comparable. The additional `german` campaign verifies German clarification,
focused comparison, approval continuation, and architecture-artifact persistence
without changing that baseline.
Fixture language uses BCP 47-style tags. The typed contract already accepts
`pt-BR`; adding Brazilian Portuguese later requires a complete response-label
catalog and its own separately selectable fixtures rather than new semantic routing.

Codex execution belongs to
[`adapters/codex/evaluations`](../../adapters/codex/evaluations/README.md), not here.

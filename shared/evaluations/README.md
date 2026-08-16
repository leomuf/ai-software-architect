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
The additional `brazilian-portuguese` campaign applies the same contract to
Brazilian Portuguese (`pt-BR`) clarification, comparison, approval continuation,
and artifact persistence without changing either established baseline.
The additional `spanish` campaign applies the same contract to neutral Spanish
(`es`) clarification, comparison, approval continuation, and artifact persistence
without changing the established baselines.
The additional `python-project-variety` campaign reviews two reproducible small
Python repositories with deliberately different shapes: a cohesive single-file CLI
and a five-file `src`-layout service. It checks whether recommendations remain
evidence-based and proportionate as repository structure changes.
Fixture language uses BCP 47-style tags. Every supported response language has a
complete response-label catalog and its own separately selectable fixtures rather
than language-specific semantic routing.

Codex execution belongs to
[`adapters/codex/evaluations`](../../adapters/codex/evaluations/README.md), not here.

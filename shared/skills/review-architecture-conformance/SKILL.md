---
name: review-architecture-conformance
description: Review code, changes, or repository structure against accepted ADRs and architecture contracts. Use when a developer asks whether an implementation conforms, has drifted, contains an accepted deviation, or requires an architecture decision update.
license: MIT
---
<!--
SPDX-FileCopyrightText: 2026 Leonardo Muffato (AUTOSOFT Engineering - www.autosoft-engineering.de)
SPDX-License-Identifier: MIT
-->

# Review Architecture Conformance

1. Establish the review scope and load the accepted contract and linked ADRs.
2. Collect the smallest relevant evidence. Prefer deterministic dependency and boundary tools when available; disclose unverified languages or truncation.
3. Link every finding to a specific rule or decision and concrete workspace-relative evidence.
4. Classify findings as confirmed violations, possible drift, or acceptable deviations. Calibrate severity and confidence independently.
5. Recommend remediation or a decision review; do not silently rewrite the architecture contract.
6. Report examined and skipped files plus truncation and tool limitations. Never use an unexplained score.

Load [finding classification](references/finding-classification.md) whenever assigning finding type, severity, or confidence.


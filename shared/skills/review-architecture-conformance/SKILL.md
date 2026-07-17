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
7. Prioritize the highest-leverage architectural improvement. Do not recommend broad restructuring when a smaller boundary or safety net addresses the evidenced risk.

## Evidence and reporting protocol

- Follow the orchestration skill's read-only analysis safety rules. Never import, execute, compile, launch, or test repository code during a read-only review.
- Reuse facts and file content already read. Avoid exploratory commands whose answer is already present in source text or deterministic evidence, and batch related static inspections when safe.
- Keep deterministic dependency analysis as supporting evidence for the architecture review, not as the user-facing objective unless the user explicitly requests a dependency scan.
- Maintain a claim ledger using `confirmed-fact`, `static-indication`, `runtime-observation`, `assumption`, and `unverified-possibility`.
- Cite the observation behind every environment, dependency, and side-effect claim. Do not infer a missing dependency solely from an unavailable command, and do not attribute an artifact to a command unless the before/after evidence supports that attribution.
- Reconcile contradictory claims before reporting. If they cannot be reconciled, present the contradiction as an unresolved limitation rather than selecting the convenient statement.
- Perform one final repository-integrity check after the last potentially mutating action and report any side effect. Do not repeat the check when no intervening action could mutate the repository.

Load [finding classification](references/finding-classification.md) whenever assigning finding type, severity, or confidence.

---
name: prepare-coding-handoff
description: Translate accepted architecture decisions and constraints into a coding-agent-ready implementation plan. Use after ADR and contract approval when another coding task needs milestones, boundaries, verification steps, sequencing, and explicit non-goals without repeating architecture analysis.
license: MIT
---
<!--
SPDX-FileCopyrightText: 2026 Leonardo Muffato (AUTOSOFT Engineering - www.autosoft-engineering.de)
SPDX-License-Identifier: MIT
-->

# Prepare Coding Handoff

1. Load only accepted ADRs, the validated contract, relevant project context, and current repository evidence.
2. Translate decisions into ordered, independently verifiable milestones.
3. Name component responsibilities, dependency constraints, data ownership, integration boundaries, quality targets, and prohibited approaches.
4. Cite the ADR or contract rule behind every material constraint.
5. Define tests and checks for each milestone, plus explicit non-goals and unresolved questions.
6. Do not redesign approved decisions or write application code. Route changed requirements back to architecture approval.
7. Scan the candidate plan for likely secrets before writing it safely.

Use the [implementation plan template](assets/implementation-plan-template.md) for structure and remove its SPDX source header from generated output. When the active host supplies this template inside one generated artifact-authoring bundle, use that already-loaded copy instead of reading the canonical source again.

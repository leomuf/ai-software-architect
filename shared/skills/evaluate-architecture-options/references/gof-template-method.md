<!-- SPDX-FileCopyrightText: 2026 Leonardo Muffato (AUTOSOFT Engineering - www.autosoft-engineering.de) | SPDX-License-Identifier: MIT -->
# Template Method
## Intent
Fix an algorithm skeleton while allowing selected steps to vary.
## Problem and forces
Workflows share sequence and invariants but differ at controlled extension points.
## Applicability
Use when inheritance is already appropriate and the stable skeleton must govern variants.
## When not to use
Avoid when runtime composition, independent step reuse, or multiple inheritance axes are needed.
## Benefits
Centralizes sequence and prevents variants from violating fixed steps.
## Liabilities
Creates inheritance coupling and fragile hooks.
## Implementation considerations
Minimize protected hooks, document call order, and prevent bypass of invariants.
## Credible alternatives
Strategy, pipeline composition, higher-order functions, or explicit orchestration.
## Related patterns
Factory Method, Strategy.
## Architecture interview questions
Which sequence is invariant, and is inheritance the correct lifetime relationship?


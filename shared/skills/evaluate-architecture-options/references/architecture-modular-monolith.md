<!-- SPDX-FileCopyrightText: 2026 Leonardo Muffato (AUTOSOFT Engineering - www.autosoft-engineering.de) | SPDX-License-Identifier: MIT -->
# Modular Monolith
## Intent
Deploy one application while enforcing cohesive modules and explicit internal boundaries.
## Problem and forces
Teams need domain separation without distributed-system cost.
## Applicability
Use when one deployment and transaction boundary fit scale and team autonomy needs.
## When not to use
Avoid when independently required deployment, isolation, ownership, or scaling is proven.
## Benefits
Simpler operations and consistency while preserving future seams.
## Liabilities
Weak enforcement can decay into a tightly coupled monolith; deployment remains shared.
## Implementation considerations
Define module APIs, data ownership, dependency rules, and boundary tests.
## Credible alternatives
Layered monolith, vertical slices, service-oriented architecture.
## Related patterns
Hexagonal Architecture, Dependency Inversion, Transactional Outbox.
## Architecture interview questions
Which modules need real autonomy, and which distributed costs are justified today?


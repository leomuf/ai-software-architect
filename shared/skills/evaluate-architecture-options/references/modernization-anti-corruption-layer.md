<!-- SPDX-FileCopyrightText: 2026 Leonardo Muffato (AUTOSOFT Engineering - www.autosoft-engineering.de) | SPDX-License-Identifier: MIT -->
# Anti-Corruption Layer
## Intent
Protect a domain model by translating to and from a legacy or external model at a deliberate boundary.
## Problem and forces
External semantics, terminology, and data shapes would otherwise distort the local domain.
## Applicability
Use when semantic translation is substantial and the local model must evolve independently.
## When not to use
Avoid when a thin Adapter or Facade is sufficient or both sides intentionally share one model.
## Benefits
Contains legacy influence and supports incremental modernization.
## Liabilities
Adds mapping, duplicated concepts, synchronization, and boundary ownership cost.
## Implementation considerations
Own canonical mappings, error semantics, identity, versioning, reconciliation, and migration exit criteria.
## Credible alternatives
Adapter, Facade, shared contract, data migration, or upstream change.
## Related patterns
Adapter, Facade, Ports and Adapters.
## Architecture interview questions
Which external concepts would corrupt local language, and who owns the translation lifecycle?


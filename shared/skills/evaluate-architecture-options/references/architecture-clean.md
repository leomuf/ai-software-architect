<!-- SPDX-FileCopyrightText: 2026 Leonardo Muffato (AUTOSOFT Engineering - www.autosoft-engineering.de) | SPDX-License-Identifier: MIT -->
# Clean Architecture
## Intent
Keep enterprise and application policy independent of delivery mechanisms and infrastructure.
## Problem and forces
Long-lived policy must survive framework, database, UI, and vendor changes.
## Applicability
Use when domain complexity and expected technology change justify explicit inward dependencies.
## When not to use
Avoid maximal rings and abstractions for simple CRUD or short-lived applications.
## Benefits
Improves policy testability and infrastructure replaceability.
## Liabilities
Can add mapping, interfaces, ceremony, and unclear duplication.
## Implementation considerations
Scale boundaries to actual volatility and enforce dependencies toward policy.
## Credible alternatives
Hexagonal, Layered, Vertical Slice, or simple modular monolith.
## Related patterns
Dependency Inversion, Repository, Adapter.
## Architecture interview questions
Which policy must outlive which concrete technologies?


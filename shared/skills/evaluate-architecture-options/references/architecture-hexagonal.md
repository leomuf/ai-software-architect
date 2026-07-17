<!-- SPDX-FileCopyrightText: 2026 Leonardo Muffato (AUTOSOFT Engineering - www.autosoft-engineering.de) | SPDX-License-Identifier: MIT -->
# Hexagonal Architecture
## Intent
Protect application behavior behind inbound and outbound ports implemented by adapters.
## Problem and forces
Multiple delivery or infrastructure mechanisms must use the same application core.
## Applicability
Use when external technology volatility and test isolation are material.
## When not to use
Avoid one interface per class or ports without a credible alternative adapter or test need.
## Benefits
Makes boundaries explicit and supports isolated application testing.
## Liabilities
Adds mapping and indirection and can become terminology without enforcement.
## Implementation considerations
Let use cases own port contracts; keep adapters outside the core.
## Credible alternatives
Clean Architecture, Layered Architecture, direct integration.
## Related patterns
Ports and Adapters, Adapter, Dependency Inversion.
## Architecture interview questions
Which external mechanisms are volatile, and what core behavior must remain independent?


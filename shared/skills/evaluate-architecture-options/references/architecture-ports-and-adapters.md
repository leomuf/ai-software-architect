<!-- SPDX-FileCopyrightText: 2026 Leonardo Muffato (AUTOSOFT Engineering - www.autosoft-engineering.de) | SPDX-License-Identifier: MIT -->
# Ports and Adapters
## Intent
Express application-facing and infrastructure-facing boundaries as ports with concrete adapters.
## Problem and forces
Core behavior must remain independent of callers and external systems.
## Applicability
Use where multiple adapters, isolated testing, or external volatility justify an explicit port.
## When not to use
Avoid ports that add only forwarding and have no consumer-owned semantics.
## Benefits
Clarifies boundary ownership and limits technology coupling.
## Liabilities
Adds interfaces, mapping, and terminology that can outgrow the problem.
## Implementation considerations
Name ports by capability, keep transport types outside, and test adapters against contracts.
## Credible alternatives
Direct integration, Facade, Layered Architecture, or simple modules.
## Related patterns
Hexagonal Architecture, Adapter, Dependency Inversion.
## Architecture interview questions
Which use case owns each port, and what adapter variation is expected?


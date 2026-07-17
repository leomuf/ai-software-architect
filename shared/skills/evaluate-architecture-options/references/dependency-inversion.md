<!-- SPDX-FileCopyrightText: 2026 Leonardo Muffato (AUTOSOFT Engineering - www.autosoft-engineering.de) | SPDX-License-Identifier: MIT -->
# Dependency Inversion
## Intent
Make high-level policy depend on abstractions it owns rather than volatile details.
## Problem and forces
Business behavior is coupled to databases, frameworks, vendors, or delivery mechanisms.
## Applicability
Use at volatility and test seams where multiple implementations or isolation have clear value.
## When not to use
Avoid interfaces that merely mirror one stable concrete class without a boundary need.
## Benefits
Protects policy and enables substitution and focused tests.
## Liabilities
Adds abstractions and composition complexity.
## Implementation considerations
Place abstractions with the consumer's policy and compose concrete implementations at the edge.
## Credible alternatives
Direct dependency, functional parameter, Adapter, or module boundary.
## Related patterns
Dependency Injection, Hexagonal Architecture, Strategy.
## Architecture interview questions
Which detail is volatile, and which policy should own the required contract?


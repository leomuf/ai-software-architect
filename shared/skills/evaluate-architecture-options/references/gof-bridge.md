<!-- SPDX-FileCopyrightText: 2026 Leonardo Muffato (AUTOSOFT Engineering - www.autosoft-engineering.de) | SPDX-License-Identifier: MIT -->
# Bridge
## Intent
Separate an abstraction from its implementation so both can vary independently.
## Problem and forces
Two orthogonal dimensions of variation would otherwise create a subclass explosion.
## Applicability
Use when both dimensions are real, stable extension axes with independent lifecycles.
## When not to use
Avoid for one implementation or speculative variation.
## Benefits
Supports independent extension and favors composition.
## Liabilities
Introduces indirection and can split concepts that users perceive as one.
## Implementation considerations
Keep the implementor interface narrow and owned by the abstraction's needs.
## Credible alternatives
Strategy, Adapter, parameterized composition, or direct implementation.
## Related patterns
Adapter, Abstract Factory, Strategy.
## Architecture interview questions
What are the two independent variation axes, and who evolves each one?


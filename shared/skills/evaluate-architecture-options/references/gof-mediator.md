<!-- SPDX-FileCopyrightText: 2026 Leonardo Muffato (AUTOSOFT Engineering - www.autosoft-engineering.de) | SPDX-License-Identifier: MIT -->
# Mediator
## Intent
Encapsulate how a set of peer objects coordinate.
## Problem and forces
Many-to-many peer interactions create tangled dependencies and duplicated coordination rules.
## Applicability
Use when a cohesive coordination protocol can be owned centrally.
## When not to use
Avoid when direct collaboration is simple or the mediator would become a god object.
## Benefits
Reduces peer coupling and centralizes interaction policy.
## Liabilities
Moves complexity into one coordinator and may reduce local comprehensibility.
## Implementation considerations
Keep domain behavior with participants and limit the mediator to coordination.
## Credible alternatives
Domain service, events, Observer, explicit workflow, or message broker.
## Related patterns
Observer, Facade.
## Architecture interview questions
Which interactions form one protocol, and how will mediator growth be bounded?


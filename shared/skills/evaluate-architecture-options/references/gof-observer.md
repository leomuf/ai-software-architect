<!-- SPDX-FileCopyrightText: 2026 Leonardo Muffato (AUTOSOFT Engineering - www.autosoft-engineering.de) | SPDX-License-Identifier: MIT -->
# Observer
## Intent
Notify registered in-process dependents when a subject changes.
## Problem and forces
One object must publish change without compile-time coupling to every reaction.
## Applicability
Use for synchronous or explicitly scheduled in-process subscriptions with bounded observers.
## When not to use
Avoid as a substitute for durable distributed messaging or when call order must stay obvious.
## Benefits
Supports extensible reactions and reduces direct publisher knowledge.
## Liabilities
Creates hidden control flow, ordering issues, lifecycle leaks, and cascading failure.
## Implementation considerations
Define sync versus async execution, ordering, unsubscribe lifecycle, errors, and reentrancy.
## Credible alternatives
Direct calls, Mediator, domain-event dispatcher, or distributed Publish/Subscribe.
## Related patterns
Mediator, Publish/Subscribe, Model-View-Controller.
## Architecture interview questions
Is delivery in-process, and what ordering, failure, and lifetime guarantees are required?


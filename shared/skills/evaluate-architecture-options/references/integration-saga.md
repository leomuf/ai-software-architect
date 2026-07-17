<!-- SPDX-FileCopyrightText: 2026 Leonardo Muffato (AUTOSOFT Engineering - www.autosoft-engineering.de) | SPDX-License-Identifier: MIT -->
# Saga
## Intent
Coordinate a multi-service business transaction through local transactions and compensating actions.
## Problem and forces
One business process spans independently owned data without a global transaction.
## Applicability
Use when eventual consistency is acceptable and compensations can be defined.
## When not to use
Avoid when one local transaction or service boundary can own the invariant.
## Benefits
Supports long-running cross-service workflows without global locking.
## Liabilities
Exposes intermediate states and adds compensation, timeout, observability, and recovery complexity.
## Implementation considerations
Choose choreography for simple decentralized flows and orchestration for explicit complex control; make steps idempotent.
## Credible alternatives
Move data ownership, local transaction, reservation, reconciliation, or process manager.
## Related patterns
Transactional Outbox, Idempotent Consumer, Command.
## Architecture interview questions
Which invariants cross services, and is every completed step meaningfully compensatable?


<!-- SPDX-FileCopyrightText: 2026 Leonardo Muffato (AUTOSOFT Engineering - www.autosoft-engineering.de) | SPDX-License-Identifier: MIT -->
# Event-Driven Architecture
## Intent
Coordinate components through facts about completed state changes.
## Problem and forces
Producers should not synchronously know every reaction and temporal decoupling is valuable.
## Applicability
Use when asynchronous reactions, extensibility, or independent availability justify eventual consistency.
## When not to use
Avoid for simple request-response flows or when immediate consistent completion is required.
## Benefits
Decouples producers, supports fan-out, and absorbs timing differences.
## Liabilities
Adds ordering, duplication, schema evolution, observability, and consistency complexity.
## Implementation considerations
Define event meaning, ownership, delivery guarantee, idempotency, ordering, and failure recovery.
## Credible alternatives
Direct calls, orchestration, queues, Observer, or scheduled batch.
## Related patterns
Publish/Subscribe, Transactional Outbox, Saga, Idempotent Consumer.
## Architecture interview questions
Which fact is published, and what consistency and delivery guarantees do consumers require?


<!-- SPDX-FileCopyrightText: 2026 Leonardo Muffato (AUTOSOFT Engineering - www.autosoft-engineering.de) | SPDX-License-Identifier: MIT -->
# Publish/Subscribe
## Intent
Distribute messages to multiple independently operating subscribers through a broker or event channel.
## Problem and forces
Publishers must not know subscribers and delivery crosses process or deployment boundaries.
## Applicability
Use when fan-out, independent consumption, and temporal decoupling justify distributed messaging.
## When not to use
Avoid for simple synchronous calls or when immediate coordinated success is required.
## Benefits
Supports extensibility and independent subscriber availability.
## Liabilities
Adds duplicate delivery, ordering, schema evolution, lag, and broker operations.
## Implementation considerations
Define topic ownership, delivery semantics, retention, compatibility, idempotency, and dead-letter handling.
## Credible alternatives
Direct request, queue, Observer for in-process notifications, or scheduled integration.
## Related patterns
Observer, Event-Driven Architecture, Idempotent Consumer.
## Architecture interview questions
Is delivery distributed, and what ordering, durability, and replay guarantees are needed?


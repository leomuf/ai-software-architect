<!-- SPDX-FileCopyrightText: 2026 Leonardo Muffato (AUTOSOFT Engineering - www.autosoft-engineering.de) | SPDX-License-Identifier: MIT -->
# Transactional Outbox
## Intent
Commit domain state and an outbound message record in one local transaction, then relay it.
## Problem and forces
Database changes and broker publication cannot safely share a distributed transaction.
## Applicability
Use when reliable event publication must follow committed state.
## When not to use
Avoid when no atomic database exists, occasional reconciliation is acceptable, or a platform provides equivalent guarantees.
## Benefits
Prevents committed state without a corresponding publish record.
## Liabilities
Adds relay lag, duplicate delivery, cleanup, ordering, and operational monitoring.
## Implementation considerations
Use an idempotent consumer, stable event identity, bounded retention, and visible relay health.
## Credible alternatives
Change-data capture, event sourcing, direct publish with reconciliation, or distributed transaction where truly supported.
## Related patterns
Unit of Work, Idempotent Consumer, Publish/Subscribe.
## Architecture interview questions
Which state and message must be atomic, and how are relay failures detected and recovered?


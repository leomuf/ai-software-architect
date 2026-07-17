<!-- SPDX-FileCopyrightText: 2026 Leonardo Muffato (AUTOSOFT Engineering - www.autosoft-engineering.de) | SPDX-License-Identifier: MIT -->
# Idempotency
## Intent
Make repeated execution with the same operation identity produce one intended effect.
## Problem and forces
Retries, duplicate requests, and uncertain responses can repeat side effects.
## Applicability
Use for retried commands, payments, provisioning, and externally visible state changes.
## When not to use
Avoid claiming idempotency when only transport deduplication exists or identities are unstable.
## Benefits
Enables safe retry and reduces duplicate effects.
## Liabilities
Requires identity storage, retention, conflict semantics, and concurrency control.
## Implementation considerations
Define key scope, payload mismatch behavior, atomic persistence, expiry, and response replay.
## Credible alternatives
At-most-once attempt, conditional update, natural unique constraint, or reconciliation.
## Related patterns
Idempotent Consumer, Retry, Transactional Outbox.
## Architecture interview questions
What identifies the same operation, and how long must duplicate detection persist?


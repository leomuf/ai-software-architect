<!-- SPDX-FileCopyrightText: 2026 Leonardo Muffato (AUTOSOFT Engineering - www.autosoft-engineering.de) | SPDX-License-Identifier: MIT -->
# Idempotent Consumer
## Intent
Process duplicate message deliveries without repeating business effects.
## Problem and forces
At-least-once brokers may redeliver after timeout, crash, or acknowledgement loss.
## Applicability
Use when consumers change state and duplicate delivery is possible.
## When not to use
Avoid relying solely on broker deduplication when business effects outlive its window.
## Benefits
Makes at-least-once delivery operationally safe.
## Liabilities
Adds inbox state, retention, contention, and message-identity requirements.
## Implementation considerations
Persist message identity atomically with effects and define replay and poison-message handling.
## Credible alternatives
Naturally idempotent update, unique constraint, reconciliation, or broker exactly-once feature with verified scope.
## Related patterns
Idempotency, Transactional Outbox, Publish/Subscribe.
## Architecture interview questions
What is the stable message identity, and can deduplication commit with the business effect?


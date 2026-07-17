<!-- SPDX-FileCopyrightText: 2026 Leonardo Muffato (AUTOSOFT Engineering - www.autosoft-engineering.de) | SPDX-License-Identifier: MIT -->
# Unit of Work
## Intent
Track changes and coordinate their persistence within one transaction boundary.
## Problem and forces
Several repositories or objects must commit atomically and consistently.
## Applicability
Use when the persistence technology does not already expose an adequate transaction/session unit.
## When not to use
Avoid wrapping an ORM unit of work with a duplicate abstraction or spanning remote services transactionally.
## Benefits
Makes commit and rollback boundaries explicit.
## Liabilities
Long units increase contention and implicit tracking can surprise callers.
## Implementation considerations
Define ownership, nesting, retries, isolation, disposal, and interaction with domain events.
## Credible alternatives
ORM session, explicit transaction function, Saga, or Transactional Outbox.
## Related patterns
Repository, Command, Transactional Outbox.
## Architecture interview questions
What must commit atomically, and which existing component already owns that transaction?


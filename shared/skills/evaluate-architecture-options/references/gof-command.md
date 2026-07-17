<!-- SPDX-FileCopyrightText: 2026 Leonardo Muffato (AUTOSOFT Engineering - www.autosoft-engineering.de) | SPDX-License-Identifier: MIT -->
# Command
## Intent
Represent a request as an object with explicit execution semantics.
## Problem and forces
Requests need queuing, logging, retry, scheduling, undo, or sender/receiver decoupling.
## Applicability
Use when request lifecycle is first-class and the command boundary has business meaning.
## When not to use
Avoid for simple direct calls or as a wrapper that adds no lifecycle behavior.
## Benefits
Enables uniform dispatch, composition, and explicit request metadata.
## Liabilities
Increases type count and can hide ordinary control flow behind a bus.
## Implementation considerations
Define idempotency, authorization, transaction boundary, result shape, and retry semantics.
## Credible alternatives
Direct method, application service, message, or Chain of Responsibility.
## Related patterns
Memento, Strategy, Chain of Responsibility.
## Architecture interview questions
Which request lifecycle capability justifies making the request an object?


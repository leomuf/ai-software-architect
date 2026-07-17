<!-- SPDX-FileCopyrightText: 2026 Leonardo Muffato (AUTOSOFT Engineering - www.autosoft-engineering.de) | SPDX-License-Identifier: MIT -->
# Chain of Responsibility
## Intent
Pass a request through ordered handlers until one or more handlers process it.
## Problem and forces
Sender and receiver selection must be decoupled and handler order may vary.
## Applicability
Use for bounded validation, policy, or processing chains with explicit continuation rules.
## When not to use
Avoid when exactly one receiver is known or silent non-handling would be unsafe.
## Benefits
Supports configurable handlers and reduces sender coupling.
## Liabilities
Order becomes behavior, tracing is harder, and requests may remain unhandled.
## Implementation considerations
Define stop versus continue semantics, default handling, observability, and cycle prevention.
## Credible alternatives
Middleware pipeline, Command dispatcher, rules engine, or direct orchestration.
## Related patterns
Command, Composite.
## Architecture interview questions
Who guarantees handling, and how is order configured and observed?


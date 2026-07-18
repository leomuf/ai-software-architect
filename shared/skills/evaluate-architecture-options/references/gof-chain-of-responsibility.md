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
## Python example
**Example context:** A support desk passes incoming messages through ordered handlers that route urgent and billing requests to the appropriate queue.

```python
from typing import Protocol


class Handler(Protocol):
    def handle(self, request: str) -> str | None: ...


class KeywordHandler:
    def __init__(self, keyword: str, result: str, next_handler: Handler | None = None) -> None:
        self.keyword = keyword
        self.result = result
        self.next_handler = next_handler

    def handle(self, request: str) -> str | None:
        if self.keyword in request:
            return self.result
        if self.next_handler is not None:
            return self.next_handler.handle(request)
        return None


chain = KeywordHandler(
    "urgent",
    "priority queue",
    KeywordHandler("billing", "billing queue"),
)
```
Each handler either processes the request or explicitly delegates to the next handler in the ordered chain.
## Credible alternatives
Middleware pipeline, Command dispatcher, rules engine, or direct orchestration.
## Related patterns
Command, Composite.
## Architecture interview questions
Who guarantees handling, and how is order configured and observed?

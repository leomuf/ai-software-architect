<!-- SPDX-FileCopyrightText: 2026 Leonardo Muffato (AUTOSOFT Engineering - www.autosoft-engineering.de) | SPDX-License-Identifier: MIT -->
# Decorator
## Intent
Add responsibilities to an object dynamically while preserving its interface.
## Problem and forces
Optional behaviors must be combined without a subclass for every combination.
## Applicability
Use for transparent, order-aware cross-cutting behavior around one interface.
## When not to use
Avoid when behavior changes the contract, type identity matters, or ordering is too implicit.
## Benefits
Supports composable responsibilities and focused classes.
## Liabilities
Creates many small objects, debugging layers, and order-dependent behavior.
## Implementation considerations
Document ordering, exception behavior, idempotence, and identity semantics.
## Python example
**Example context:** A text-processing pipeline wraps an in-memory data source with optional uppercase and bracket formatting operations.

```python
from dataclasses import dataclass
from typing import Protocol


class DataSource(Protocol):
    def read(self) -> str: ...


@dataclass(frozen=True)
class MemorySource:
    value: str

    def read(self) -> str:
        return self.value


@dataclass(frozen=True)
class UppercaseDecorator:
    wrapped: DataSource

    def read(self) -> str:
        return self.wrapped.read().upper()


@dataclass(frozen=True)
class BracketDecorator:
    wrapped: DataSource

    def read(self) -> str:
        return f"[{self.wrapped.read()}]"
```
Both decorators preserve `DataSource` while adding stackable behavior whose order remains visible at composition.
## Credible alternatives
Middleware pipeline, Strategy, explicit orchestration, or inheritance.
## Related patterns
Adapter, Composite, Proxy.
## Architecture interview questions
Which behaviors compose, and does their order change correctness?

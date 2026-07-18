<!-- SPDX-FileCopyrightText: 2026 Leonardo Muffato (AUTOSOFT Engineering - www.autosoft-engineering.de) | SPDX-License-Identifier: MIT -->
# Singleton
## Intent
Provide controlled access to one instance within a defined process scope.
## Problem and forces
A resource appears unique and callers need coordinated access.
## Applicability
Use rarely, when process-wide uniqueness is a proven invariant and lifecycle is explicit.
## When not to use
Avoid as global dependency access, for distributed uniqueness, or merely to save allocations.
## Benefits
Can enforce one in-process coordinator and centralize lifecycle.
## Liabilities
Creates hidden coupling, test interference, concurrency hazards, and misleading cross-process assumptions.
## Implementation considerations
Define scope, thread safety, initialization failure, reset policy, and disposal.
## Python example
**Example context:** An application exposes one process-wide configuration store while retaining an explicit reset hook for isolated tests.

```python
from __future__ import annotations


class Configuration:
    _instance: Configuration | None = None

    def __new__(cls) -> Configuration:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.values = {}
        return cls._instance

    @classmethod
    def reset_for_tests(cls) -> None:
        cls._instance = None

    values: dict[str, str]
```
`Configuration` controls one instance inside the Python process and exposes an explicit reset solely for isolated tests.
## Credible alternatives
Dependency injection, module-owned instance, scoped container, or external coordination service.
## Related patterns
Abstract Factory, Facade.
## Architecture interview questions
What proves uniqueness is required, and is the boundary a thread, process, tenant, or deployment?

<!-- SPDX-FileCopyrightText: 2026 Leonardo Muffato (AUTOSOFT Engineering - www.autosoft-engineering.de) | SPDX-License-Identifier: MIT -->
# Proxy
## Intent
Use a stand-in to control access to another object.
## Problem and forces
Access requires lazy creation, authorization, remote communication, caching, or lifecycle control.
## Applicability
Use when the stand-in preserves the subject contract and control behavior is explicit.
## When not to use
Avoid when remote or failure semantics make local transparency misleading.
## Benefits
Centralizes access control or lifecycle behavior behind a compatible interface.
## Liabilities
Adds latency and failure invisibly and can confuse identity or equality.
## Implementation considerations
Expose material remote, cache, timeout, and authorization semantics.
## Python example
**Example context:** An image viewer delays creating the real image object until a client first asks for its dimensions.

```python
from typing import Protocol


class Image(Protocol):
    def dimensions(self) -> tuple[int, int]: ...


class RealImage:
    def __init__(self, width: int, height: int) -> None:
        self._dimensions = (width, height)

    def dimensions(self) -> tuple[int, int]:
        return self._dimensions


class LazyImageProxy:
    def __init__(self, width: int, height: int) -> None:
        self._width = width
        self._height = height
        self._subject: RealImage | None = None

    def dimensions(self) -> tuple[int, int]:
        if self._subject is None:
            self._subject = RealImage(self._width, self._height)
        return self._subject.dimensions()
```
`LazyImageProxy` preserves the `Image` contract while controlling when the real subject is created.
## Credible alternatives
Decorator, Adapter, explicit gateway, or direct access.
## Related patterns
Adapter, Decorator.
## Architecture interview questions
What access must be controlled, and which nonlocal semantics must remain visible?

<!-- SPDX-FileCopyrightText: 2026 Leonardo Muffato (AUTOSOFT Engineering - www.autosoft-engineering.de) | SPDX-License-Identifier: MIT -->
# Builder
## Intent
Separate construction steps from the final representation.
## Problem and forces
Creating a valid object requires ordered steps, optional parts, or multiple representations.
## Applicability
Use for complex immutable objects, readable staged construction, or reusable construction processes.
## When not to use
Avoid when a constructor or named factory is already clear and invariants are simple.
## Benefits
Improves construction readability and can enforce staged invariants.
## Liabilities
Adds types, mutable intermediate state, and possible invalid partial builders.
## Implementation considerations
Validate at build time, keep required fields explicit, and avoid exposing incomplete products.
## Python example
**Example context:** A reporting application constructs an immutable report step by step and validates that its required title is present.

```python
from dataclasses import dataclass


@dataclass(frozen=True)
class Report:
    title: str
    sections: tuple[str, ...]


class ReportBuilder:
    def __init__(self) -> None:
        self._title: str | None = None
        self._sections: list[str] = []

    def titled(self, title: str) -> "ReportBuilder":
        self._title = title
        return self

    def add_section(self, text: str) -> "ReportBuilder":
        self._sections.append(text)
        return self

    def build(self) -> Report:
        if self._title is None:
            raise ValueError("title is required")
        return Report(self._title, tuple(self._sections))
```
`ReportBuilder` holds staged construction state and creates an immutable, validated `Report` only at `build()`.
## Credible alternatives
Named constructors, Factory Method, parameter objects, or serialization schemas.
## Related patterns
Abstract Factory, Composite.
## Architecture interview questions
Which construction steps vary, and when must validity be enforced?

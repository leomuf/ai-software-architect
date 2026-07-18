<!-- SPDX-FileCopyrightText: 2026 Leonardo Muffato (AUTOSOFT Engineering - www.autosoft-engineering.de) | SPDX-License-Identifier: MIT -->
# Iterator
## Intent
Traverse aggregate elements without exposing internal representation.
## Problem and forces
Clients need consistent traversal while collections retain representation freedom.
## Applicability
Use when custom traversal, lazy access, or multiple traversal strategies are meaningful.
## When not to use
Avoid custom iterators when the language's standard iteration protocol is sufficient.
## Benefits
Separates traversal from storage and supports lazy consumption.
## Liabilities
Mutation, resource lifetime, and concurrent traversal semantics become complex.
## Implementation considerations
Define ordering, snapshot behavior, cancellation, errors, and resource disposal.
## Python example
**Example context:** A numeric range library lets callers traverse a sequence while hiding how traversal state is stored.

```python
from collections.abc import Iterator


class NumberIterator(Iterator[int]):
    def __init__(self, start: int, stop: int) -> None:
        self._current = start
        self._stop = stop

    def __next__(self) -> int:
        if self._current >= self._stop:
            raise StopIteration
        value = self._current
        self._current += 1
        return value


class NumberRange:
    def __init__(self, start: int, stop: int) -> None:
        self._start = start
        self._stop = stop

    def __iter__(self) -> NumberIterator:
        return NumberIterator(self._start, self._stop)
```
`NumberIterator` owns traversal state while `NumberRange` keeps its representation behind Python's iteration protocol.
## Credible alternatives
Standard collections, generators, streams, or query APIs.
## Related patterns
Composite, Visitor.
## Architecture interview questions
What traversal differs from the platform standard, and can the aggregate mutate during it?

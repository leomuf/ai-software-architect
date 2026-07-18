<!-- SPDX-FileCopyrightText: 2026 Leonardo Muffato (AUTOSOFT Engineering - www.autosoft-engineering.de) | SPDX-License-Identifier: MIT -->
# Flyweight
## Intent
Share intrinsic state across many fine-grained objects while supplying extrinsic state per use.
## Problem and forces
Object count and duplicated immutable state cause measured memory pressure.
## Applicability
Use only after profiling proves high cardinality and a safe intrinsic/extrinsic split.
## When not to use
Avoid when state is mutable, identity matters, or memory pressure is speculative.
## Benefits
Can substantially reduce duplicated memory.
## Liabilities
Complicates state management, concurrency, and call sites.
## Implementation considerations
Make shared state immutable and bound cache growth and eviction.
## Python example
**Example context:** A text editor reduces memory use by sharing identical font styles among many independently positioned glyphs.

```python
from dataclasses import dataclass


@dataclass(frozen=True)
class TextStyle:
    font: str
    size: int
    color: str


class StyleFactory:
    def __init__(self) -> None:
        self._styles: dict[tuple[str, int, str], TextStyle] = {}

    def get(self, font: str, size: int, color: str) -> TextStyle:
        key = (font, size, color)
        if key not in self._styles:
            self._styles[key] = TextStyle(*key)
        return self._styles[key]


@dataclass(frozen=True)
class Glyph:
    character: str
    x: int
    y: int
    style: TextStyle
```
`TextStyle` is shared intrinsic state, while each `Glyph` retains its extrinsic character and position.
## Credible alternatives
Interning, value objects, compression, batching, or simpler caching.
## Related patterns
Factory, Composite.
## Architecture interview questions
What profiling evidence exists, and which state is safely immutable and shareable?

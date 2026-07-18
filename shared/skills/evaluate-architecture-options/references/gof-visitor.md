<!-- SPDX-FileCopyrightText: 2026 Leonardo Muffato (AUTOSOFT Engineering - www.autosoft-engineering.de) | SPDX-License-Identifier: MIT -->
# Visitor
## Intent
Add operations across a stable object structure without modifying each element class.
## Problem and forces
Many unrelated operations traverse a closed set of element types.
## Applicability
Use when element types change rarely but operations are added often and double dispatch is acceptable.
## When not to use
Avoid when element types evolve frequently, encapsulation would be broken, or pattern matching is clearer.
## Benefits
Groups each cross-cutting operation and supports type-specific behavior.
## Liabilities
Adding an element type changes every visitor and may expose element internals.
## Implementation considerations
Define fallback behavior, traversal ownership, result aggregation, and version compatibility.
## Python example
**Example context:** An arithmetic expression model adds an evaluation operation across number and addition nodes without placing that operation in their data.

```python
from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


class Visitor(Protocol):
    def visit_number(self, number: Number) -> int: ...
    def visit_add(self, addition: Add) -> int: ...


class Expression(Protocol):
    def accept(self, visitor: Visitor) -> int: ...


@dataclass(frozen=True)
class Number:
    value: int

    def accept(self, visitor: Visitor) -> int:
        return visitor.visit_number(self)


@dataclass(frozen=True)
class Add:
    left: Expression
    right: Expression

    def accept(self, visitor: Visitor) -> int:
        return visitor.visit_add(self)


class Evaluator:
    def visit_number(self, number: Number) -> int:
        return number.value

    def visit_add(self, addition: Add) -> int:
        return addition.left.accept(self) + addition.right.accept(self)
```
Elements dispatch to type-specific visitor methods, allowing `Evaluator` to add an operation without changing their stored data.
## Credible alternatives
Methods on elements, pattern matching, external functions, Interpreter, or data-oriented transforms.
## Related patterns
Composite, Iterator, Interpreter.
## Architecture interview questions
Which axis changes more often: element types or operations?

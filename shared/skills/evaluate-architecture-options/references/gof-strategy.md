<!-- SPDX-FileCopyrightText: 2026 Leonardo Muffato (AUTOSOFT Engineering - www.autosoft-engineering.de) | SPDX-License-Identifier: MIT -->
# Strategy
## Intent
Encapsulate interchangeable algorithms behind one contract.
## Problem and forces
Behavior varies by policy, tenant, configuration, or test while callers remain stable.
## Applicability
Use when multiple meaningful algorithms share inputs, outputs, and substitutability expectations.
## When not to use
Avoid for one implementation, trivial conditionals, or variants with incompatible semantics.
## Benefits
Supports composition, focused testing, and runtime policy selection.
## Liabilities
Adds indirection and moves selection complexity to a composition point.
## Implementation considerations
Define behavioral invariants, selection ownership, failure semantics, and statefulness.
## Python example
**Example context:** An online checkout calculates a total using a selectable discount policy, such as no discount or ten percent off.

```python
from dataclasses import dataclass
from typing import Protocol


class Discount(Protocol):
    def apply(self, subtotal: int) -> int: ...


class NoDiscount:
    def apply(self, subtotal: int) -> int:
        return subtotal


class TenPercentDiscount:
    def apply(self, subtotal: int) -> int:
        return subtotal * 90 // 100


@dataclass(frozen=True)
class Checkout:
    discount: Discount

    def total(self, subtotal: int) -> int:
        if subtotal < 0:
            raise ValueError("subtotal cannot be negative")
        return self.discount.apply(subtotal)
```
`Checkout` stays stable while interchangeable discount strategies encapsulate the varying algorithm.
## Credible alternatives
Direct conditional, Template Method, command function, or rules table.
## Related patterns
State, Bridge, Template Method.
## Architecture interview questions
Which algorithms are truly substitutable, and who owns selection and configuration?

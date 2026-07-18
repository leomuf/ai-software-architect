<!-- SPDX-FileCopyrightText: 2026 Leonardo Muffato (AUTOSOFT Engineering - www.autosoft-engineering.de) | SPDX-License-Identifier: MIT -->
# State
## Intent
Delegate state-dependent behavior to objects representing states.
## Problem and forces
Behavior changes across explicit states and conditionals are growing or transition rules need focus.
## Applicability
Use when states, transitions, and per-state behavior are meaningful domain concepts.
## When not to use
Avoid for a few stable conditionals or when state is merely data without behavior.
## Benefits
Localizes state behavior and makes transitions explicit.
## Liabilities
Adds classes and can scatter the overall transition graph.
## Implementation considerations
Centralize allowed transitions, handle invalid transitions, persistence, concurrency, and recovery.
## Python example
**Example context:** A vending machine changes how it responds to coin insertion and product selection depending on whether credit is available.

```python
from __future__ import annotations

from typing import Protocol


class State(Protocol):
    def insert_coin(self, machine: VendingMachine) -> None: ...
    def select(self, machine: VendingMachine) -> str: ...


class VendingMachine:
    def __init__(self) -> None:
        self.state: State = Waiting()

    def insert_coin(self) -> None:
        self.state.insert_coin(self)

    def select(self) -> str:
        return self.state.select(self)


class Waiting:
    def insert_coin(self, machine: VendingMachine) -> None:
        machine.state = HasCredit()

    def select(self, machine: VendingMachine) -> str:
        return "insert coin"


class HasCredit:
    def insert_coin(self, machine: VendingMachine) -> None:
        raise ValueError("credit already available")

    def select(self, machine: VendingMachine) -> str:
        machine.state = Waiting()
        return "dispensed"
```
`VendingMachine` delegates behavior to its current state, and each state makes valid transitions explicit.
## Credible alternatives
Table-driven state machine, Strategy, enum switch, or workflow engine.
## Related patterns
Strategy, Flyweight.
## Architecture interview questions
What are the valid transitions, and must state survive process or deployment boundaries?

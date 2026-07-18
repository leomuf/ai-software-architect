<!-- SPDX-FileCopyrightText: 2026 Leonardo Muffato (AUTOSOFT Engineering - www.autosoft-engineering.de) | SPDX-License-Identifier: MIT -->
# Command
## Intent
Represent a request as an object with explicit execution semantics.
## Problem and forces
Requests need queuing, logging, retry, scheduling, undo, or sender/receiver decoupling.
## Applicability
Use when request lifecycle is first-class and the command boundary has business meaning.
## When not to use
Avoid for simple direct calls or as a wrapper that adds no lifecycle behavior.
## Benefits
Enables uniform dispatch, composition, and explicit request metadata.
## Liabilities
Increases type count and can hide ordinary control flow behind a bus.
## Implementation considerations
Define idempotency, authorization, transaction boundary, result shape, and retry semantics.
## Python example
**Example context:** A remote-control application packages the action of turning on a light so the control can invoke it without knowing the device API.

```python
from dataclasses import dataclass
from typing import Protocol


class Command(Protocol):
    def execute(self) -> None: ...


class Light:
    def __init__(self) -> None:
        self.is_on = False

    def turn_on(self) -> None:
        self.is_on = True


@dataclass
class TurnOnLight:
    light: Light

    def execute(self) -> None:
        self.light.turn_on()


@dataclass
class RemoteControl:
    command: Command

    def press(self) -> None:
        self.command.execute()
```
`TurnOnLight` turns a receiver operation into a first-class request that the invoker can store or dispatch uniformly.
## Credible alternatives
Direct method, application service, message, or Chain of Responsibility.
## Related patterns
Memento, Strategy, Chain of Responsibility.
## Architecture interview questions
Which request lifecycle capability justifies making the request an object?

<!-- SPDX-FileCopyrightText: 2026 Leonardo Muffato (AUTOSOFT Engineering - www.autosoft-engineering.de) | SPDX-License-Identifier: MIT -->
# Mediator
## Intent
Encapsulate how a set of peer objects coordinate.
## Problem and forces
Many-to-many peer interactions create tangled dependencies and duplicated coordination rules.
## Applicability
Use when a cohesive coordination protocol can be owned centrally.
## When not to use
Avoid when direct collaboration is simple or the mediator would become a god object.
## Benefits
Reduces peer coupling and centralizes interaction policy.
## Liabilities
Moves complexity into one coordinator and may reduce local comprehensibility.
## Implementation considerations
Keep domain behavior with participants and limit the mediator to coordination.
## Python example
**Example context:** A login dialog enables its submit button when the username field becomes non-empty, without directly coupling the two widgets.

```python
from typing import Protocol


class Mediator(Protocol):
    def notify(self, sender: object, event: str) -> None: ...


class TextBox:
    def __init__(self, mediator: Mediator) -> None:
        self.text = ""
        self.mediator = mediator

    def change(self, text: str) -> None:
        self.text = text
        self.mediator.notify(self, "changed")


class Button:
    def __init__(self) -> None:
        self.enabled = False


class LoginDialog:
    def __init__(self) -> None:
        self.button = Button()
        self.username = TextBox(self)

    def notify(self, sender: object, event: str) -> None:
        if sender is self.username and event == "changed":
            self.button.enabled = bool(self.username.text.strip())
```
`LoginDialog` centralizes coordination between peer widgets without making them depend directly on one another.
## Credible alternatives
Domain service, events, Observer, explicit workflow, or message broker.
## Related patterns
Observer, Facade.
## Architecture interview questions
Which interactions form one protocol, and how will mediator growth be bounded?

<!-- SPDX-FileCopyrightText: 2026 Leonardo Muffato (AUTOSOFT Engineering - www.autosoft-engineering.de) | SPDX-License-Identifier: MIT -->
# Memento
## Intent
Capture restorable object state without exposing its internal representation.
## Problem and forces
Undo, rollback, or snapshots require state restoration while preserving encapsulation.
## Applicability
Use for bounded in-process state whose consistency and ownership are explicit.
## When not to use
Avoid for durable audit, distributed rollback, large sensitive state, or event history.
## Benefits
Supports restoration without public setters for internal state.
## Liabilities
Snapshots consume memory and can retain sensitive or obsolete resources.
## Implementation considerations
Version snapshots, bound retention, protect confidentiality, and validate restoration compatibility.
## Python example
**Example context:** A text editor captures snapshots of its content so a separate history component can later restore an earlier version.

```python
from dataclasses import dataclass


@dataclass(frozen=True)
class EditorMemento:
    text: str


class Editor:
    def __init__(self) -> None:
        self._text = ""

    def replace(self, text: str) -> None:
        self._text = text

    def snapshot(self) -> EditorMemento:
        return EditorMemento(self._text)

    def restore(self, memento: EditorMemento) -> None:
        self._text = memento.text


class History:
    def __init__(self) -> None:
        self._entries: list[EditorMemento] = []

    def save(self, memento: EditorMemento) -> None:
        self._entries.append(memento)

    def latest(self) -> EditorMemento:
        return self._entries[-1]
```
`Editor` creates and consumes its opaque snapshot, while `History` stores snapshots without editing their state.
## Credible alternatives
Command undo, event sourcing, database transaction, or recomputation.
## Related patterns
Command, Prototype.
## Architecture interview questions
What must be restored, for how long, and is a snapshot legally and operationally safe?

<!-- SPDX-FileCopyrightText: 2026 Leonardo Muffato (AUTOSOFT Engineering - www.autosoft-engineering.de) | SPDX-License-Identifier: MIT -->
# Abstract Factory
## Intent
Create compatible families of related objects without naming concrete classes at call sites.
## Problem and forces
Product variants must remain mutually consistent while clients stay independent of construction details.
## Applicability
Use when a runtime or deployment selects an entire product family and family consistency matters.
## When not to use
Avoid for one product type, stable concrete construction, or variants that change independently.
## Benefits
Centralizes family selection and prevents accidental mixing.
## Liabilities
Adds interfaces and makes adding a new product kind expensive across every family.
## Implementation considerations
Keep factory methods cohesive; validate that every family supplies the same product set.
## Python example
**Example context:** A settings screen creates matching light- or dark-theme buttons and checkboxes without coupling the screen to concrete widgets.

```python
from typing import Protocol

class Button(Protocol):
    def render(self) -> str: ...

class Checkbox(Protocol):
    def render(self) -> str: ...

class LightButton:
    def render(self) -> str:
        return "light button"

class LightCheckbox:
    def render(self) -> str:
        return "light checkbox"


class DarkButton:
    def render(self) -> str:
        return "dark button"


class DarkCheckbox:
    def render(self) -> str:
        return "dark checkbox"


class WidgetFactory(Protocol):
    def create_button(self) -> Button: ...
    def create_checkbox(self) -> Checkbox: ...


class LightWidgetFactory:
    def create_button(self) -> Button:
        return LightButton()

    def create_checkbox(self) -> Checkbox:
        return LightCheckbox()


class DarkWidgetFactory:
    def create_button(self) -> Button:
        return DarkButton()

    def create_checkbox(self) -> Checkbox:
        return DarkCheckbox()


def render_settings(factory: WidgetFactory) -> tuple[str, str]:
    return factory.create_button().render(), factory.create_checkbox().render()
```
`WidgetFactory` creates one compatible product family; the client uses only the abstract product contracts.
## Credible alternatives
Factory Method, Builder, dependency-injection composition, or explicit constructors.
## Related patterns
Factory Method, Prototype, Singleton.
## Architecture interview questions
Which products must vary together, and what failure occurs if families are mixed?

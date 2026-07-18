<!-- SPDX-FileCopyrightText: 2026 Leonardo Muffato (AUTOSOFT Engineering - www.autosoft-engineering.de) | SPDX-License-Identifier: MIT -->
# Factory Method
## Intent
Define a creation operation while allowing an implementation or subclass to choose the concrete product.
## Problem and forces
Client workflow is stable but the created collaborator varies by extension or environment.
## Applicability
Use when creation is a deliberate extension point and the product interface is meaningful.
## When not to use
Avoid when direct construction or dependency injection communicates the choice more clearly.
## Benefits
Localizes concrete creation and supports controlled extension.
## Liabilities
Can create unnecessary inheritance or obscure the composition root.
## Implementation considerations
Prefer an explicit callable factory over subclassing when inheritance adds no other value.
## Python example
**Example context:** A data-import application keeps its import workflow stable while specialized importers choose the parser for a file format.

```python
from abc import ABC, abstractmethod
from typing import Protocol


class Parser(Protocol):
    def parse(self, text: str) -> list[str]: ...


class CsvParser:
    def parse(self, text: str) -> list[str]:
        return text.split(",")


class Importer(ABC):
    def import_text(self, text: str) -> list[str]:
        return self.create_parser().parse(text)

    @abstractmethod
    def create_parser(self) -> Parser:
        raise NotImplementedError


class CsvImporter(Importer):
    def create_parser(self) -> Parser:
        return CsvParser()
```
`Importer` owns the stable workflow while its factory method lets a subclass select the concrete parser.
## Credible alternatives
Abstract Factory, dependency injection, explicit constructors, or registry lookup.
## Related patterns
Abstract Factory, Template Method.
## Architecture interview questions
Who owns the creation choice, and is that choice an actual extension point?

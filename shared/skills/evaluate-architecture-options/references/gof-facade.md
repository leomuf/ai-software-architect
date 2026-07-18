<!-- SPDX-FileCopyrightText: 2026 Leonardo Muffato (AUTOSOFT Engineering - www.autosoft-engineering.de) | SPDX-License-Identifier: MIT -->
# Facade
## Intent
Provide a simpler, stable entry point to a complex subsystem.
## Problem and forces
Most clients need a coordinated subset of subsystem operations without internal coupling.
## Applicability
Use at subsystem boundaries with common use cases and a meaningful simplified contract.
## When not to use
Avoid as a god object or when clients genuinely require the full subsystem model.
## Benefits
Reduces coupling and provides a migration or layering seam.
## Liabilities
May accumulate unrelated workflows or hide important operational controls.
## Implementation considerations
Keep the facade cohesive; allow advanced access only through explicit interfaces.
## Python example
**Example context:** A text-conversion service exposes one operation that decodes input, normalizes whitespace, and encodes the result.

```python
class Decoder:
    def decode(self, source: bytes) -> str:
        return source.decode("utf-8")


class Normalizer:
    def normalize(self, text: str) -> str:
        return " ".join(text.split())


class Encoder:
    def encode(self, text: str) -> bytes:
        return text.encode("utf-8")


class TextConversionFacade:
    def __init__(self) -> None:
        self._decoder = Decoder()
        self._normalizer = Normalizer()
        self._encoder = Encoder()

    def convert(self, source: bytes) -> bytes:
        text = self._decoder.decode(source)
        normalized = self._normalizer.normalize(text)
        return self._encoder.encode(normalized)
```
`TextConversionFacade` provides one cohesive operation while coordinating the more detailed subsystem.
## Credible alternatives
Application service, Adapter, Anti-Corruption Layer, or direct subsystem APIs.
## Related patterns
Mediator, Adapter, Singleton.
## Architecture interview questions
Which common client workflows justify one stable entry point?

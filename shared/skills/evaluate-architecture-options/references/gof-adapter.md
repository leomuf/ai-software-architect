<!-- SPDX-FileCopyrightText: 2026 Leonardo Muffato (AUTOSOFT Engineering - www.autosoft-engineering.de) | SPDX-License-Identifier: MIT -->
# Adapter
## Intent
Translate an existing interface into the interface a client expects.
## Problem and forces
Useful existing code or an external API has incompatible operations or representations.
## Applicability
Use at a concrete integration seam where translation preserves clear domain-facing semantics.
## When not to use
Avoid when interfaces can be changed directly or translation would hide incompatible behavior.
## Benefits
Contains vendor or legacy coupling and improves substitutability.
## Liabilities
Adds indirection and may become a leaky pass-through or oversized translation layer.
## Implementation considerations
Map errors, data ownership, timeouts, and semantic differences explicitly.
## Python example
**Example context:** A temperature-monitoring application expects Celsius readings but must integrate a legacy sensor that reports Fahrenheit.

```python
from dataclasses import dataclass
from typing import Protocol


class CelsiusSensor(Protocol):
    def read_celsius(self) -> float: ...


class LegacyFahrenheitSensor:
    def read_fahrenheit(self) -> float:
        return 77.0


@dataclass
class FahrenheitAdapter:
    legacy: LegacyFahrenheitSensor

    def read_celsius(self) -> float:
        return (self.legacy.read_fahrenheit() - 32) * 5 / 9


def current_temperature(sensor: CelsiusSensor) -> float:
    return sensor.read_celsius()
```
`FahrenheitAdapter` translates the legacy operation and representation into the domain-facing `CelsiusSensor` contract.
## Credible alternatives
Facade, Anti-Corruption Layer, direct integration, or generated client boundary.
## Related patterns
Bridge, Decorator, Proxy.
## Architecture interview questions
Which semantic differences require translation rather than simple signature conversion?

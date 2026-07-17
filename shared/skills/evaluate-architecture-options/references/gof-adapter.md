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
## Credible alternatives
Facade, Anti-Corruption Layer, direct integration, or generated client boundary.
## Related patterns
Bridge, Decorator, Proxy.
## Architecture interview questions
Which semantic differences require translation rather than simple signature conversion?


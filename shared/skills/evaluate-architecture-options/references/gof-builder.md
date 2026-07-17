<!-- SPDX-FileCopyrightText: 2026 Leonardo Muffato (AUTOSOFT Engineering - www.autosoft-engineering.de) | SPDX-License-Identifier: MIT -->
# Builder
## Intent
Separate construction steps from the final representation.
## Problem and forces
Creating a valid object requires ordered steps, optional parts, or multiple representations.
## Applicability
Use for complex immutable objects, readable staged construction, or reusable construction processes.
## When not to use
Avoid when a constructor or named factory is already clear and invariants are simple.
## Benefits
Improves construction readability and can enforce staged invariants.
## Liabilities
Adds types, mutable intermediate state, and possible invalid partial builders.
## Implementation considerations
Validate at build time, keep required fields explicit, and avoid exposing incomplete products.
## Credible alternatives
Named constructors, Factory Method, parameter objects, or serialization schemas.
## Related patterns
Abstract Factory, Composite.
## Architecture interview questions
Which construction steps vary, and when must validity be enforced?


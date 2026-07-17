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
## Credible alternatives
Application service, Adapter, Anti-Corruption Layer, or direct subsystem APIs.
## Related patterns
Mediator, Adapter, Singleton.
## Architecture interview questions
Which common client workflows justify one stable entry point?


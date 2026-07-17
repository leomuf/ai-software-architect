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
## Credible alternatives
Abstract Factory, dependency injection, explicit constructors, or registry lookup.
## Related patterns
Abstract Factory, Template Method.
## Architecture interview questions
Who owns the creation choice, and is that choice an actual extension point?


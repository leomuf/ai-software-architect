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
## Credible alternatives
Factory Method, Builder, dependency-injection composition, or explicit constructors.
## Related patterns
Factory Method, Prototype, Singleton.
## Architecture interview questions
Which products must vary together, and what failure occurs if families are mixed?


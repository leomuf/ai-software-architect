<!-- SPDX-FileCopyrightText: 2026 Leonardo Muffato (AUTOSOFT Engineering - www.autosoft-engineering.de) | SPDX-License-Identifier: MIT -->
# Repository
## Intent
Expose domain-oriented collection operations while containing persistence mechanics.
## Problem and forces
Domain logic needs retrieval and persistence without query or storage details leaking inward.
## Applicability
Use for aggregate-oriented domain models and meaningful persistence substitution or isolation.
## When not to use
Avoid generic CRUD wrappers over an ORM that add no domain semantics.
## Benefits
Clarifies persistence boundary and centralizes domain-specific queries.
## Liabilities
Can hide query cost, duplicate ORM capabilities, and create inefficient abstractions.
## Implementation considerations
Align methods with aggregates and use cases; expose pagination and consistency explicitly.
## Credible alternatives
Direct ORM, query service, data mapper, or gateway.
## Related patterns
Unit of Work, Dependency Inversion, Adapter.
## Architecture interview questions
Which domain operations need persistence independence, and does the ORM already provide the boundary?


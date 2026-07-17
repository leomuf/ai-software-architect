<!-- SPDX-FileCopyrightText: 2026 Leonardo Muffato (AUTOSOFT Engineering - www.autosoft-engineering.de) | SPDX-License-Identifier: MIT -->
# Iterator
## Intent
Traverse aggregate elements without exposing internal representation.
## Problem and forces
Clients need consistent traversal while collections retain representation freedom.
## Applicability
Use when custom traversal, lazy access, or multiple traversal strategies are meaningful.
## When not to use
Avoid custom iterators when the language's standard iteration protocol is sufficient.
## Benefits
Separates traversal from storage and supports lazy consumption.
## Liabilities
Mutation, resource lifetime, and concurrent traversal semantics become complex.
## Implementation considerations
Define ordering, snapshot behavior, cancellation, errors, and resource disposal.
## Credible alternatives
Standard collections, generators, streams, or query APIs.
## Related patterns
Composite, Visitor.
## Architecture interview questions
What traversal differs from the platform standard, and can the aggregate mutate during it?


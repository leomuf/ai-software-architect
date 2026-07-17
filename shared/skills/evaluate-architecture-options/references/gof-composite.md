<!-- SPDX-FileCopyrightText: 2026 Leonardo Muffato (AUTOSOFT Engineering - www.autosoft-engineering.de) | SPDX-License-Identifier: MIT -->
# Composite
## Intent
Treat individual objects and compositions uniformly through a part-whole tree.
## Problem and forces
Clients must perform the same operation on leaves and nested groups.
## Applicability
Use when the domain is genuinely hierarchical and uniform operations have coherent semantics.
## When not to use
Avoid when leaf and container behavior differs materially or arbitrary nesting is unsafe.
## Benefits
Simplifies tree traversal and recursive composition.
## Liabilities
Can weaken type distinctions and make constraints on valid children difficult.
## Implementation considerations
Define ownership, cycle prevention, traversal cost, mutation, and partial-failure behavior.
## Credible alternatives
Explicit tree nodes, Visitor, flat collections, or domain-specific aggregates.
## Related patterns
Decorator, Iterator, Visitor.
## Architecture interview questions
Which operations are truly uniform, and what child combinations are invalid?


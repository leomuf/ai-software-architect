<!-- SPDX-FileCopyrightText: 2026 Leonardo Muffato (AUTOSOFT Engineering - www.autosoft-engineering.de) | SPDX-License-Identifier: MIT -->
# Flyweight
## Intent
Share intrinsic state across many fine-grained objects while supplying extrinsic state per use.
## Problem and forces
Object count and duplicated immutable state cause measured memory pressure.
## Applicability
Use only after profiling proves high cardinality and a safe intrinsic/extrinsic split.
## When not to use
Avoid when state is mutable, identity matters, or memory pressure is speculative.
## Benefits
Can substantially reduce duplicated memory.
## Liabilities
Complicates state management, concurrency, and call sites.
## Implementation considerations
Make shared state immutable and bound cache growth and eviction.
## Credible alternatives
Interning, value objects, compression, batching, or simpler caching.
## Related patterns
Factory, Composite.
## Architecture interview questions
What profiling evidence exists, and which state is safely immutable and shareable?


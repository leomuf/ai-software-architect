<!-- SPDX-FileCopyrightText: 2026 Leonardo Muffato (AUTOSOFT Engineering - www.autosoft-engineering.de) | SPDX-License-Identifier: MIT -->
# Visitor
## Intent
Add operations across a stable object structure without modifying each element class.
## Problem and forces
Many unrelated operations traverse a closed set of element types.
## Applicability
Use when element types change rarely but operations are added often and double dispatch is acceptable.
## When not to use
Avoid when element types evolve frequently, encapsulation would be broken, or pattern matching is clearer.
## Benefits
Groups each cross-cutting operation and supports type-specific behavior.
## Liabilities
Adding an element type changes every visitor and may expose element internals.
## Implementation considerations
Define fallback behavior, traversal ownership, result aggregation, and version compatibility.
## Credible alternatives
Methods on elements, pattern matching, external functions, Interpreter, or data-oriented transforms.
## Related patterns
Composite, Iterator, Interpreter.
## Architecture interview questions
Which axis changes more often: element types or operations?


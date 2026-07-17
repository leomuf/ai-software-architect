<!-- SPDX-FileCopyrightText: 2026 Leonardo Muffato (AUTOSOFT Engineering - www.autosoft-engineering.de) | SPDX-License-Identifier: MIT -->
# Interpreter
## Intent
Represent and evaluate sentences in a small grammar through object structure.
## Problem and forces
A stable, limited language must be parsed and evaluated repeatedly.
## Applicability
Use for small grammars where direct representation improves domain clarity.
## When not to use
Avoid complex, evolving, performance-sensitive, or security-critical languages.
## Benefits
Makes grammar rules explicit and composable.
## Liabilities
Class count and evaluation complexity grow quickly with grammar size.
## Implementation considerations
Use a real parser, bound input, reject ambiguous syntax, and never evaluate generated code.
## Credible alternatives
Parser generator, table-driven evaluator, rules engine, or existing language.
## Related patterns
Composite, Visitor.
## Architecture interview questions
How large and stable is the grammar, and what hostile input must be handled?


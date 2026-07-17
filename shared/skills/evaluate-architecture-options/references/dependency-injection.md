<!-- SPDX-FileCopyrightText: 2026 Leonardo Muffato (AUTOSOFT Engineering - www.autosoft-engineering.de) | SPDX-License-Identifier: MIT -->
# Dependency Injection
## Intent
Supply collaborators from outside an object instead of constructing or locating them internally.
## Problem and forces
Lifecycle and implementation choice need centralized composition and test substitution.
## Applicability
Use constructor injection by default; use factories for runtime creation and containers where object graphs justify them.
## When not to use
Avoid service-locator access, ambient container calls, or injection of trivial values without clarity.
## Benefits
Makes dependencies visible and separates use from construction.
## Liabilities
Large graphs and containers can obscure lifecycle and startup failures.
## Implementation considerations
Keep one composition root, validate graphs at startup, and declare scope and disposal.
## Credible alternatives
Explicit construction, module functions, Factory Method, or parameter passing.
## Related patterns
Dependency Inversion, Factory Method, Strategy.
## Architecture interview questions
Which lifecycles and implementations vary, and can explicit construction remain clearer than a container?


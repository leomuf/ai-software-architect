<!-- SPDX-FileCopyrightText: 2026 Leonardo Muffato (AUTOSOFT Engineering - www.autosoft-engineering.de) | SPDX-License-Identifier: MIT -->
# Layered Architecture
## Intent
Organize technical responsibilities into layers with controlled dependency direction.
## Problem and forces
Presentation, application, domain, and infrastructure concerns need separation and reuse.
## Applicability
Use when technical layers are stable mental models and dependency rules are enforceable.
## When not to use
Avoid rigid layers that make each feature cross many files or permit pass-through ceremony.
## Benefits
Clarifies technical responsibility and can isolate infrastructure.
## Liabilities
Encourages horizontal coupling, anemic domains, and changes spanning every layer.
## Implementation considerations
Define allowed dependencies, bypass rules, and where business behavior resides.
## Credible alternatives
Vertical slice, Clean, Hexagonal, or simple modular structure.
## Related patterns
Dependency Inversion, Repository, Facade.
## Architecture interview questions
Do changes align with layers or with features, and which dependencies must be prohibited?


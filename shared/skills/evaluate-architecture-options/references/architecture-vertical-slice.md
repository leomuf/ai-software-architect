<!-- SPDX-FileCopyrightText: 2026 Leonardo Muffato (AUTOSOFT Engineering - www.autosoft-engineering.de) | SPDX-License-Identifier: MIT -->
# Vertical Slice Architecture
## Intent
Organize code by feature or use case so a change is locally cohesive.
## Problem and forces
Feature work repeatedly crosses technical layers and unrelated features evolve differently.
## Applicability
Use when feature autonomy and local reasoning matter more than horizontal reuse.
## When not to use
Avoid duplicating critical policy or infrastructure without intentional shared boundaries.
## Benefits
Localizes change and lets slices choose proportionate internal structure.
## Liabilities
May duplicate code and create inconsistent conventions across slices.
## Implementation considerations
Define slice ownership, shared-kernel criteria, and cross-slice communication rules.
## Credible alternatives
Layered architecture, modular monolith, application services.
## Related patterns
Command, Mediator, Modular Monolith.
## Architecture interview questions
Do most changes stay within one feature, and what must genuinely be shared?


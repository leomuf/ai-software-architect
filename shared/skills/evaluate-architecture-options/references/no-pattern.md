<!-- SPDX-FileCopyrightText: 2026 Leonardo Muffato (AUTOSOFT Engineering - www.autosoft-engineering.de) | SPDX-License-Identifier: MIT -->
# No Named Pattern
## Intent
Keep the design direct when no demonstrated force justifies additional structure.
## Problem and forces
Pattern familiarity can create speculative abstractions and accidental complexity.
## Applicability
Prefer direct code for one stable case with low change cost and clear ownership.
## When not to use
Do not use simplicity as an excuse to ignore known variation, boundaries, or quality risks.
## Benefits
Minimizes concepts, code, maintenance, and premature commitments.
## Liabilities
Later change may require refactoring if assumptions prove false.
## Implementation considerations
Record the assumptions and the measurable trigger for introducing structure later.
## Credible alternatives
The smallest focused pattern that addresses a current, evidenced force.
## Related patterns
YAGNI, evolutionary design, Architecture Decision Records.
## Architecture interview questions
Which present requirement fails without the proposed abstraction?


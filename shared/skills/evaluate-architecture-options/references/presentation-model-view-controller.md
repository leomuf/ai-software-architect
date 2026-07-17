<!-- SPDX-FileCopyrightText: 2026 Leonardo Muffato (AUTOSOFT Engineering - www.autosoft-engineering.de) | SPDX-License-Identifier: MIT -->
# Model-View-Controller
## Intent
Separate presentation input coordination, presentation rendering, and application or domain state.
## Problem and forces
UI interaction and rendering must change without absorbing business behavior.
## Applicability
Use for server-rendered applications or frameworks whose request lifecycle fits explicit controllers and views.
## When not to use
Avoid assuming that having framework controllers proves a complete MVC design; client components may fit other models.
## Benefits
Clarifies presentation roles and supports independent rendering and interaction tests.
## Liabilities
Controllers can become business-logic containers and models can become ambiguous bags of UI data.
## Implementation considerations
Keep controllers thin, views presentation-only, and business rules in application or domain services. Distinguish server-side MVC from client-side interpretations.
## Credible alternatives
MVVM for binding-heavy clients, MVP for testable passive views, Presentation Model, or component-based UI architecture.
## Related patterns
Observer, Strategy, Application Service.
## Architecture interview questions
Where does UI state live, who handles input, and how are business rules kept out of controllers and views?


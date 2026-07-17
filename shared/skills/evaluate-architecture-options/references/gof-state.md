<!-- SPDX-FileCopyrightText: 2026 Leonardo Muffato (AUTOSOFT Engineering - www.autosoft-engineering.de) | SPDX-License-Identifier: MIT -->
# State
## Intent
Delegate state-dependent behavior to objects representing states.
## Problem and forces
Behavior changes across explicit states and conditionals are growing or transition rules need focus.
## Applicability
Use when states, transitions, and per-state behavior are meaningful domain concepts.
## When not to use
Avoid for a few stable conditionals or when state is merely data without behavior.
## Benefits
Localizes state behavior and makes transitions explicit.
## Liabilities
Adds classes and can scatter the overall transition graph.
## Implementation considerations
Centralize allowed transitions, handle invalid transitions, persistence, concurrency, and recovery.
## Credible alternatives
Table-driven state machine, Strategy, enum switch, or workflow engine.
## Related patterns
Strategy, Flyweight.
## Architecture interview questions
What are the valid transitions, and must state survive process or deployment boundaries?


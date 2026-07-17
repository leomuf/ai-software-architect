<!-- SPDX-FileCopyrightText: 2026 Leonardo Muffato (AUTOSOFT Engineering - www.autosoft-engineering.de) | SPDX-License-Identifier: MIT -->
# Memento
## Intent
Capture restorable object state without exposing its internal representation.
## Problem and forces
Undo, rollback, or snapshots require state restoration while preserving encapsulation.
## Applicability
Use for bounded in-process state whose consistency and ownership are explicit.
## When not to use
Avoid for durable audit, distributed rollback, large sensitive state, or event history.
## Benefits
Supports restoration without public setters for internal state.
## Liabilities
Snapshots consume memory and can retain sensitive or obsolete resources.
## Implementation considerations
Version snapshots, bound retention, protect confidentiality, and validate restoration compatibility.
## Credible alternatives
Command undo, event sourcing, database transaction, or recomputation.
## Related patterns
Command, Prototype.
## Architecture interview questions
What must be restored, for how long, and is a snapshot legally and operationally safe?


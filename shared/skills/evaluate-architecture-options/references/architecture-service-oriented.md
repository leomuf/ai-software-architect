<!-- SPDX-FileCopyrightText: 2026 Leonardo Muffato (AUTOSOFT Engineering - www.autosoft-engineering.de) | SPDX-License-Identifier: MIT -->
# Service-Oriented Architecture
## Intent
Partition capabilities into independently owned services with explicit network contracts.
## Problem and forces
Capabilities need independent deployment, scaling, failure isolation, or organizational ownership.
## Applicability
Use when those benefits outweigh network, consistency, security, and operational costs.
## When not to use
Avoid for speculative scale, small tightly coupled teams, or transaction-heavy boundaries.
## Benefits
Enables independent evolution and targeted scaling or isolation.
## Liabilities
Adds partial failure, latency, versioning, observability, and distributed data consistency.
## Implementation considerations
Align boundaries with ownership; define contracts, SLOs, data ownership, and failure handling.
## Credible alternatives
Modular monolith, vertical slices, coarse-grained services.
## Related patterns
Saga, Publish/Subscribe, Circuit Breaker, Anti-Corruption Layer.
## Architecture interview questions
Which capability requires independent ownership or deployment, and what evidence supports it?


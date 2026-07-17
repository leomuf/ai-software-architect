<!-- SPDX-FileCopyrightText: 2026 Leonardo Muffato (AUTOSOFT Engineering - www.autosoft-engineering.de) | SPDX-License-Identifier: MIT -->
# Circuit Breaker
## Intent
Temporarily stop calls to a repeatedly failing dependency and probe recovery deliberately.
## Problem and forces
Persistent failures cause resource exhaustion and retry storms.
## Applicability
Use for remote dependencies where fast rejection and a recovery probe improve system stability.
## When not to use
Avoid local deterministic errors, one-off calls, or thresholds without operational ownership.
## Benefits
Reduces cascading failure and shortens failure response time.
## Liabilities
Thresholds can flap, state may be misleading across instances, and fallback can hide outage.
## Implementation considerations
Define failure classification, rolling window, open duration, half-open probes, metrics, and fallback semantics.
## Credible alternatives
Fail fast, rate limiting, bulkhead, timeout, or queue.
## Related patterns
Retry and Backoff, Timeout and Deadline.
## Architecture interview questions
Which failures count, where does breaker state live, and what is safe while open?


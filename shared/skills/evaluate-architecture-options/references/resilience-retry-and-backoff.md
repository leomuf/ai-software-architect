<!-- SPDX-FileCopyrightText: 2026 Leonardo Muffato (AUTOSOFT Engineering - www.autosoft-engineering.de) | SPDX-License-Identifier: MIT -->
# Retry and Backoff
## Intent
Repeat a failed operation after controlled delays when failure is likely transient.
## Problem and forces
Short-lived network or dependency failures may recover without user intervention.
## Applicability
Use only for classified transient failures and idempotent or safely deduplicated operations.
## When not to use
Avoid permanent errors, validation failures, overload without coordination, or unsafe side effects.
## Benefits
Improves resilience to brief faults.
## Liabilities
Amplifies load, latency, and duplicate effects and can hide persistent failure.
## Implementation considerations
Use bounded exponential backoff with jitter, a total deadline, attempt telemetry, and retry budgets.
## Credible alternatives
Fail fast, queue for later, Circuit Breaker, fallback, or operator recovery.
## Related patterns
Timeout and Deadline, Circuit Breaker, Idempotency.
## Architecture interview questions
Which errors are transient, and what total latency and amplification budget is safe?


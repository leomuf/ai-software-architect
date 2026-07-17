<!-- SPDX-FileCopyrightText: 2026 Leonardo Muffato (AUTOSOFT Engineering - www.autosoft-engineering.de) | SPDX-License-Identifier: MIT -->
# Timeout and Deadline Propagation
## Intent
Bound waiting and propagate remaining time across dependent operations.
## Problem and forces
Unbounded waits consume resources and downstream calls can outlive the user's useful budget.
## Applicability
Use for every remote or potentially blocking dependency with a justified latency budget.
## When not to use
Avoid one arbitrary timeout copied across operations with different service objectives.
## Benefits
Limits resource retention and supports predictable failure.
## Liabilities
Incorrect values cause premature failure or continued overload.
## Implementation considerations
Prefer an end-to-end deadline, reserve cleanup time, cancel downstream work, and observe timeout causes.
## Credible alternatives
Asynchronous queue, polling, streaming, or explicit long-running job contract.
## Related patterns
Retry and Backoff, Circuit Breaker.
## Architecture interview questions
What is the end-to-end latency budget, and how is remaining time propagated?


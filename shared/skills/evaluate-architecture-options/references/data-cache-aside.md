<!-- SPDX-FileCopyrightText: 2026 Leonardo Muffato (AUTOSOFT Engineering - www.autosoft-engineering.de) | SPDX-License-Identifier: MIT -->
# Cache-Aside
## Intent
Let the application load data into a cache on misses and invalidate or refresh it after changes.
## Problem and forces
Repeated reads need lower latency or backend load at acceptable staleness.
## Applicability
Use after measurement for read-heavy data with clear keys, expiry, and consistency tolerance.
## When not to use
Avoid highly sensitive, rapidly changing, low-reuse, or strongly consistent data without safeguards.
## Benefits
Improves read latency and reduces backend load with incremental adoption.
## Liabilities
Adds invalidation, stale reads, stampedes, memory cost, and sensitive-data exposure.
## Implementation considerations
Define TTL, invalidation, negative caching, stampede control, key isolation, encryption, and metrics.
## Credible alternatives
Database tuning, materialized view, CDN, request coalescing, or no cache.
## Related patterns
Proxy, Flyweight.
## Architecture interview questions
What measured bottleneck exists, how stale may data be, and may the data legally be cached?


<!-- SPDX-FileCopyrightText: 2026 Leonardo Muffato (AUTOSOFT Engineering - www.autosoft-engineering.de) | SPDX-License-Identifier: MIT -->
# Proxy
## Intent
Use a stand-in to control access to another object.
## Problem and forces
Access requires lazy creation, authorization, remote communication, caching, or lifecycle control.
## Applicability
Use when the stand-in preserves the subject contract and control behavior is explicit.
## When not to use
Avoid when remote or failure semantics make local transparency misleading.
## Benefits
Centralizes access control or lifecycle behavior behind a compatible interface.
## Liabilities
Adds latency and failure invisibly and can confuse identity or equality.
## Implementation considerations
Expose material remote, cache, timeout, and authorization semantics.
## Credible alternatives
Decorator, Adapter, explicit gateway, or direct access.
## Related patterns
Adapter, Decorator.
## Architecture interview questions
What access must be controlled, and which nonlocal semantics must remain visible?


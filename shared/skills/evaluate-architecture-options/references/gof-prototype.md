<!-- SPDX-FileCopyrightText: 2026 Leonardo Muffato (AUTOSOFT Engineering - www.autosoft-engineering.de) | SPDX-License-Identifier: MIT -->
# Prototype
## Intent
Create objects by copying a configured exemplar.
## Problem and forces
Construction is expensive or runtime types and configuration are easier to preserve through cloning.
## Applicability
Use when copy semantics are well-defined and exemplars are safer than repeated configuration.
## When not to use
Avoid with identity-bound resources, unclear deep-copy ownership, or sensitive mutable state.
## Benefits
Reduces repeated setup and supports runtime-selected concrete types.
## Liabilities
Correct deep copying is difficult and can duplicate resources or secrets unexpectedly.
## Implementation considerations
Document deep versus shallow fields and reset identity, handles, and lifecycle state.
## Credible alternatives
Factory Method, serialization, immutable value objects, or cached configuration.
## Related patterns
Abstract Factory, Memento.
## Architecture interview questions
What state is safe to copy, and which identity or resource fields must be regenerated?


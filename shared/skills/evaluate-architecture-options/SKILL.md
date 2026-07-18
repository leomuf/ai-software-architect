---
name: evaluate-architecture-options
description: Compare credible architecture styles, design patterns, integration approaches, and no-pattern alternatives against explicit forces. Use when an architecture interview has enough context to evaluate structural choices, dependencies, data access, messaging, resilience, modernization, or presentation design.
license: MIT
---
<!--
SPDX-FileCopyrightText: 2026 Leonardo Muffato (AUTOSOFT Engineering - www.autosoft-engineering.de)
SPDX-License-Identifier: MIT
-->

# Evaluate Architecture Options

## Mandatory final-answer gate for an open selection

Treat questions such as "which design patterns should I use?" as an open selection, not as permission to output a prioritized stack of complementary patterns. If a missing fact can materially change the option set, ask a focused clarification question instead of selecting.

Before sending a final selection answer, verify that it uses these sections in this order:

1. `Decision scope and criteria`
2. `Evidence and assumptions`
3. `Alternatives`
4. `Recommendation`
5. `Supporting patterns`
6. `Your decision`

In `Alternatives`, compare three to five credible options that solve the same decision when that many exist. Use a table or equally explicit structure containing, for every option: categorized and linked name, ordinal `NN/100` fit, fit rationale, main benefit, main liability, and material assumption. When fewer than three credible alternatives exist, say why. Never count supporting patterns as alternatives merely to reach the target.

End `Your decision` by asking the user to approve, revise, or request more information. Do not continue to ADR creation or implementation without that response.

1. Start from recorded constraints, risks, stakeholders, and ranked quality attributes.
2. For an open-ended architecture or pattern-selection request, form three to five credible options within each material decision scope. Never pad the comparison with an option that does not address the same decision; when fewer than three credible alternatives exist, present the smaller set and explain why.
3. Load only references implicated by the current forces. Do not preload the catalog.
4. Compare benefits, liabilities, risks, assumptions, reversibility, and measurable fit. Scores support explanation; they do not replace it.
5. Include [no pattern](references/no-pattern.md) whenever added structure lacks a demonstrated force.
6. Recommend one option only when the evidence supports it. State uncertainty and identify decisions requiring approval.
7. Keep alternative options separate from complementary supporting patterns. Do not compare an application architecture, a presentation pattern, and an object-design pattern as if they solve the same decision.
8. Do not equate similarly named patterns across process or deployment boundaries.

## User-facing comparison contract

- Present alternatives before the recommendation. For every option show a `0–100` fit score, concise rationale, main benefit, main liability, and material assumption.
- Describe the score as an ordinal fit score for this decision, not a probability or calibrated percentage. State the criteria used to score the options.
- In `Evidence and assumptions`, distinguish static source observations from assumptions and unverified possibilities. Do not present a runtime claim unless runtime behavior was legitimately observed within the authorized mode.
- Prefix the first mention of every named option and supporting pattern with its category: `[GoF]`, `[Architecture]`, `[Presentation]`, `[Dependency]`, `[Data]`, `[Integration]`, `[Resilience]`, `[Modernization]`, or `[No pattern]`.
- Link the first user-facing pattern name to its canonical public reference under `https://github.com/leomuf/ai-software-architect/blob/main/shared/skills/evaluate-architecture-options/references/`, using the routed reference filename. Use plain text if the host cannot render Markdown links.
- For supporting patterns, add a one-line role explaining where each applies. Do not assign them competing fit scores unless they are genuine alternatives within the same decision.

## Implementation example requests

- When the user asks for a generic Python implementation example of a GoF pattern, load only that routed `gof-*.md` reference and reuse its `Python example`. Explain briefly how the example's participants map to the pattern.
- Reproduce the canonical example when a generic example is sufficient. For a repository-specific request, adapt the example to the user's domain and clearly identify the adaptation instead of presenting the canonical snippet as project-ready code.
- Do not load unrelated pattern files or synthesize additional variants unless the user asks for them or a materially different variant is necessary.

## Direct reference routing

### Object design

- Families of related products: [Abstract Factory](references/gof-abstract-factory.md)
- Object construction with many steps or variants: [Builder](references/gof-builder.md)
- Subclass- or implementation-selected creation: [Factory Method](references/gof-factory-method.md)
- Copy-based creation: [Prototype](references/gof-prototype.md)
- One process-wide instance: [Singleton](references/gof-singleton.md)
- Incompatible object interfaces: [Adapter](references/gof-adapter.md)
- Independent abstraction and implementation variation: [Bridge](references/gof-bridge.md)
- Part-whole trees: [Composite](references/gof-composite.md)
- Stackable responsibilities: [Decorator](references/gof-decorator.md)
- Simplified subsystem entry point: [Facade](references/gof-facade.md)
- Shared immutable fine-grained state: [Flyweight](references/gof-flyweight.md)
- Controlled stand-in: [Proxy](references/gof-proxy.md)
- Ordered request handlers: [Chain of Responsibility](references/gof-chain-of-responsibility.md)
- Requests as objects: [Command](references/gof-command.md)
- Small stable grammar: [Interpreter](references/gof-interpreter.md)
- Traversal without representation exposure: [Iterator](references/gof-iterator.md)
- Centralized peer coordination: [Mediator](references/gof-mediator.md)
- Captured restorable state: [Memento](references/gof-memento.md)
- In-process subscriptions: [Observer](references/gof-observer.md)
- State-dependent behavior: [State](references/gof-state.md)
- Interchangeable algorithms: [Strategy](references/gof-strategy.md)
- Fixed algorithm skeleton with variable steps: [Template Method](references/gof-template-method.md)
- New operations over stable object structures: [Visitor](references/gof-visitor.md)

### Application and presentation architecture

- One deployable with enforced modules: [Modular monolith](references/architecture-modular-monolith.md)
- Independent service ownership or deployment: [Service-oriented](references/architecture-service-oriented.md)
- Technical responsibility layers: [Layered](references/architecture-layered.md)
- Enterprise policy isolated from delivery details: [Clean](references/architecture-clean.md)
- Domain surrounded by ports: [Hexagonal](references/architecture-hexagonal.md)
- Feature-oriented change: [Vertical slice](references/architecture-vertical-slice.md)
- Event-centric decoupling: [Event-driven](references/architecture-event-driven.md)
- Server-rendered or framework presentation separation: [MVC](references/presentation-model-view-controller.md)

### Dependencies, data, integration, and resilience

- Policy depending on abstractions: [Dependency inversion](references/dependency-inversion.md)
- Supplying collaborators: [Dependency injection](references/dependency-injection.md)
- Explicit application boundaries: [Ports and adapters](references/architecture-ports-and-adapters.md)
- Data access collection abstraction: [Repository](references/data-repository.md)
- Transaction coordination: [Unit of Work](references/data-unit-of-work.md)
- Duplicate-safe operations: [Idempotency](references/integration-idempotency.md)
- Duplicate message delivery: [Idempotent Consumer](references/integration-idempotent-consumer.md)
- Atomic state and message publication: [Transactional Outbox](references/integration-transactional-outbox.md)
- Multi-service consistency: [Saga](references/integration-saga.md)
- Distributed event subscribers: [Publish/Subscribe](references/integration-publish-subscribe.md)
- Transient remote failures: [Retry and backoff](references/resilience-retry-and-backoff.md)
- Bounded waiting: [Timeout and deadline](references/resilience-timeout-and-deadline.md)
- Repeated downstream failure: [Circuit Breaker](references/resilience-circuit-breaker.md)
- Read-performance cache: [Cache-Aside](references/data-cache-aside.md)
- Legacy or external model isolation: [Anti-Corruption Layer](references/modernization-anti-corruption-layer.md)

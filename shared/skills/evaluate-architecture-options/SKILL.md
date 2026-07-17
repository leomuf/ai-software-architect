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

1. Start from recorded constraints, risks, stakeholders, and ranked quality attributes.
2. Form at least two credible options when genuine alternatives exist. Include [no pattern](references/no-pattern.md) whenever added structure lacks a demonstrated force.
3. Load only references implicated by the current forces. Do not preload the catalog.
4. Compare benefits, liabilities, risks, assumptions, reversibility, and measurable fit. Scores support explanation; they do not replace it.
5. Recommend one option only when the evidence supports it. State uncertainty and identify decisions requiring approval.
6. Do not equate similarly named patterns across process or deployment boundaries.

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


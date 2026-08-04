---
name: evaluate-architecture-options
description: Suggest and compare project-fit architecture styles, design patterns, integration approaches, and no-pattern alternatives against explicit forces. Use when enough context is available to evaluate structural choices, dependencies, data access, messaging, resilience, modernization, or presentation design.
license: MIT
---
<!--
SPDX-FileCopyrightText: 2026 Leonardo Muffato (AUTOSOFT Engineering - www.autosoft-engineering.de)
SPDX-License-Identifier: MIT
-->

# Evaluate Architecture Options

## Evidence before inspection

Apply the orchestration evidence sufficiency gate before reading the active repository or calling a tool. If the user has already supplied enough constraints to judge proportionality, treat those constraints as assumptions and answer from them. Do not inspect a project merely because the task is project-bound or repository access is available.

Use repository evidence only when implementation facts could materially change the option set or the user requests review, verification, or repository-specific advice. Tool availability is not evidence of need.

Treat a request to improve or choose patterns for "this" or the current application, project, repository, or codebase as repository-specific advice. Inspect the smallest relevant source set with host-native static reads before recommending unless the user forbids inspection or has already supplied complete decision evidence. Do not claim that repository evidence was unavailable when relevant workspace files were accessible.

## Mandatory final-answer gate for an open selection

Treat questions such as "which design patterns should I use?" as an open selection, not as permission to output a prioritized stack of complementary patterns. If a missing fact can materially change the option set and no responsible default follows from current evidence, ask a focused clarification question and end the current turn without an option comparison, recommendation, or repository inspection.

Rank alternatives from observed repository evidence and user-supplied current forces. Unverified future growth MUST NOT by itself make a heavier pattern outrank the proportionate option supported now. Show such growth as an explicit sensitivity condition: explain which future force would change the recommendation and which alternative would then become preferable. Ask one focused clarification instead only when the unknown prevents any responsible current-evidence default. Never invent likely growth to justify a pattern.

Before sending a final selection answer, verify that it uses these sections in this order:

1. `Decision scope and criteria`
2. `Evidence and assumptions`
3. `Alternatives`
4. `Recommendation`
5. `Supporting patterns`
6. `Your decision`

In `Alternatives`, compare three to five credible options that solve the same decision when that many exist. Inside `Decision scope and criteria`, explicitly state that Fit is an ordinal score for this decision and is not a probability or measured percentage. Use a table or equally explicit structure containing, for every option: categorized and linked name, ordinal `NN/100` fit, fit rationale, main benefit, main liability, and material assumption. When fewer than three credible alternatives exist, say why. Never count supporting patterns as alternatives merely to reach the target.

For a routine small-repository comparison with three alternatives, target 350 to 450 visible words for the complete six-section answer. Keep evidence bullets and table cells compact, limit supporting patterns to those that materially help the decision, and avoid repeating the same observation in the rationale and recommendation. This is a soft synthesis budget, not permission to omit required evidence, trade-offs, uncertainty, links, or decision guidance. Exceed it only when additional decision-relevant evidence is necessary.

End `Your decision` by asking the user to approve, revise, or request more information. Do not continue to ADR creation or implementation without that response.

A recommendation to keep the current simple structure or use no named pattern is still a proposed architecture decision. Explain the future force that would justify more structure, then visibly ask the user to approve, revise, or request more information. Do not omit the decision handoff merely because the recommendation adds nothing.

Use this compact response template exactly for an open selection:

```markdown
## Decision scope and criteria
<one decision and its ordinal scoring criteria>

## Evidence and assumptions
<confirmed/static evidence, then explicit assumptions and unknowns>

## Alternatives
| Option | Fit | Rationale | Main benefit | Main liability | Material assumption |
| --- | ---: | --- | --- | --- | --- |
| [Category] [Linked name] | NN/100 | ... | ... | ... | ... |

## Recommendation
<the exact category and option name from one Alternatives row, uncertainty, and why the trade-off is justified>

## Supporting patterns
- [Category] [Linked name] — <its non-competing role>

## Your decision
Please approve, revise, or request more information before I continue.
```

Shape the same content as `ArchitectureOptionComparison` when a structured output is requested, including the language-neutral `offered_actions` values `approve`, `revise`, and `more-information`. Validate that complete shape in host-native structured-output mode. In Markdown, express those choices as ordinary visible guidance rather than machine-readable comments.

Before sending the answer, perform the same deterministic rendering self-check used by the Codex control plane: all six headings appear in order, `## Decision scope and criteria` explicitly says Fit is ordinal and not a probability or measured percentage, two to five genuine alternatives are rendered (normally three to five when that many are credible), category labels and canonical links are present, the recommendation repeats one exact table option, and the final section contains visible decision guidance. Do not emit internal control markers or HTML comments; Codex may display them to the user. When the Codex Composite routes here for a comparison, a trusted Stop hook may request one complete corrected rendering.

1. Start from recorded constraints, risks, stakeholders, and ranked quality attributes.
2. For an open-ended architecture or pattern-selection request, form three to five credible options within each material decision scope. Never pad the comparison with an option that does not address the same decision; when fewer than three credible alternatives exist, present the smaller set and explain why.
3. Load only references implicated by the current forces. Do not preload the catalog.
4. Compare benefits, liabilities, risks, assumptions, reversibility, and measurable fit. Scores support explanation; they do not replace it.
5. Include [no pattern](references/no-pattern.md) whenever added structure lacks a demonstrated force.
6. Recommend one option only when current evidence supports it. Keep unverified future growth conditional rather than using it to outrank the currently proportionate choice. State uncertainty and identify decisions requiring approval.
7. Keep alternative options separate from complementary supporting patterns. Do not compare an application architecture, a presentation pattern, and an object-design pattern as if they solve the same decision.
8. Do not equate similarly named patterns across process or deployment boundaries.

## User-facing comparison contract

- Present alternatives before the recommendation. For every option show a `0–100` fit score, concise rationale, main benefit, main liability, and material assumption.
- Describe the score as an ordinal fit score for this decision, not a probability or calibrated percentage. State the criteria used to score the options.
- In `Evidence and assumptions`, distinguish static source observations from assumptions and unverified possibilities. Do not present a runtime claim unless runtime behavior was legitimately observed within the authorized mode.
- Prefix the first mention of every named option and supporting pattern with its category: `[GoF]`, `[Architecture]`, `[Presentation]`, `[Dependency]`, `[Data]`, `[Integration]`, `[Resilience]`, `[Modernization]`, or `[No pattern]`.
- Link the first user-facing pattern name to its canonical public reference under `https://github.com/leomuf/ai-software-architect/blob/main/shared/skills/evaluate-architecture-options/references/`, using the routed reference filename. Use plain text if the host cannot render Markdown links.
- For supporting patterns, add a one-line role explaining where each applies. Do not assign them competing fit scores unless they are genuine alternatives within the same decision.
- Apply the same category-and-link rule when mentioning a canonical pattern only to discourage or defer it. Do not end a section with a bare list such as `Avoid Repository, Unit of Work, and MVC`; either render each named pattern with its category and canonical link or describe the rejected abstraction types generically without naming catalog entries.

## Implementation example requests

- Treat loading the routed reference as a hard gate before answering a named-pattern explanation or implementation-example request. Do not answer from model memory. If the reference cannot be loaded, disclose that limitation instead of synthesizing an example.
- When the user asks for a generic Python implementation example of a GoF pattern, load only that routed `gof-*.md` reference and reuse its `Python example` verbatim. Explain briefly how the example's participants map to the pattern.
- In Codex, users invoke only `$ai-software-architect`. The Composite routes pattern explanations, implementation examples, and comparisons to this canonical module and uses its copied references without attempting sibling-skill activation.
- Reproduce the canonical example when a generic example is sufficient. For a repository-specific request, adapt the example to the user's domain and clearly identify the adaptation instead of presenting the canonical snippet as project-ready code.
- Do not load unrelated pattern files or synthesize additional variants unless the user asks for them or a materially different variant is necessary.
- Construct canonical public links from the routed filenames below. Do not browse or search the public repository merely to verify those deterministic links.
- Generic pattern explanations, implementation examples, and architecture guidance use the routed skill reference directly and need no deterministic tool call.

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

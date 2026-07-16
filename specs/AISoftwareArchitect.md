# AI Software Architect

## Specification Status

This document defines the product direction and first implementation scope for the OpenAI Build Week project.

The initial implementation target is an installable Codex plugin. The product is designed so that adapters for GitHub Copilot, Claude Code, Google Antigravity, and other coding assistants can reuse the same architectural skills, schemas, templates, and repository artifacts later.

## Vision

AI Software Architect is a host-native architectural reasoning agent that helps developers make explicit, well-supported architectural decisions before and during implementation.

It collaborates with coding assistants such as OpenAI Codex, GitHub Copilot, Claude Code, Google Antigravity, Cursor, JetBrains AI Assistant, Gemini Code Assist, and Windsurf. Instead of replacing those assistants or providing its own hosted model, it extends the assistant the developer already uses.

The coding assistant remains the runtime:

- It supplies the model and reasoning capability.
- It uses the user's existing subscription, credits, or API configuration.
- It reads and modifies the local repository using its native tools.
- It applies the AI Software Architect's workflows and modular skills.

AI Software Architect supplies the architectural method, knowledge, structured artifacts, and validation workflow.

The goal is to move AI-assisted development from immediate code generation toward **architecture-driven development**.

## Problem Statement

AI coding assistants are effective at generating and modifying code, but architectural decisions are often left implicit.

For example, when asked to build a notification system, an assistant may immediately produce working code without explicitly examining:

- the forces and constraints that shape the solution;
- whether a design pattern is justified;
- which architectural alternatives are viable;
- the trade-offs of each alternative;
- which decision should be recorded for future developers;
- whether the implementation continues to respect the chosen architecture.

Developers can explicitly ask a general-purpose assistant for this analysis, but the quality and structure depend on the prompt. There is no consistent architecture-first workflow, durable decision record, or reusable conformance process.

## Product Definition

AI Software Architect is an agent role implemented inside each supported coding assistant. It uses modular Agent Skills and repository-based state to perform a repeatable architecture workflow.

The agent:

1. Analyzes project requirements and available repository context.
2. Identifies ambiguities, architectural forces, risks, and quality attributes.
3. Asks focused clarification questions when necessary.
4. Produces viable architectural options rather than jumping to one pattern.
5. Recommends an approach and explains its reasoning and trade-offs.
6. Records accepted decisions as Architecture Decision Records (ADRs).
7. Produces a machine-readable architecture contract and a coding-agent handoff.
8. Reviews implementation changes for conformance when requested.
9. Updates architectural records as the project evolves.

## Confirmed Product Decisions

### Host-native model execution

AI Software Architect does not operate a hosted LLM service. Architectural reasoning is performed by the user's selected coding assistant and model.

Consequences:

- Codex users use their Codex model and credits.
- GitHub Copilot users use their Copilot plan and selected model.
- Claude Code users use their Claude configuration.
- Antigravity users use their configured Gemini model and Google account allocation.
- Recommendations may differ between assistants and models. This is acceptable.

### No managed remote MCP service

The project will not require or maintain a Streamable HTTP MCP server.

There is no central service, account system, hosted database, usage metering, or project-data upload requirement.

### No separate model API key

The core product must not ask users for an additional OpenAI, Anthropic, Google, or other model-provider API key. Model authentication remains the responsibility of the coding assistant.

Optional third-party integrations may use credentials supplied through the assistant's existing secret or environment configuration. Credentials must never be stored in project artifacts or committed to source control.

### Repository-based project state

Architectural context and decisions are stored as human-readable and machine-readable files in the user's repository. The repository is the portable source of architectural truth.

### Modular Agent Skills

Architectural knowledge and repeatable workflows are packaged as modular skills using the open `SKILL.md` format wherever the host supports it.

### Optional local MCP utilities

A local STDIO MCP server is not required for the first version. It may be added later for deterministic analysis that is not reliably implemented through prompts and native filesystem tools.

If added, it must:

- run locally;
- make no model calls;
- require no hosted service;
- use the host's MCP lifecycle;
- expose deterministic tools only;
- avoid collecting credentials or telemetry by default.

## Goals

- Make architectural decisions explicit before substantial code generation.
- Help developers compare credible alternatives and understand trade-offs.
- Generate durable ADRs and implementation constraints.
- Provide coding assistants with a clear architectural handoff.
- Detect likely architecture drift during implementation.
- Teach architectural reasoning without reducing the product to documentation.
- Remain open-source, local-first, and inspectable.
- Reuse the same knowledge and artifact formats across multiple coding assistants.

## Non-goals for the First Version

- Operating a hosted agent or MCP service.
- Providing identical reasoning across different models.
- Replacing the user's coding assistant.
- Automatically implementing the entire application.
- Supporting every architectural pattern, framework, and programming language.
- Guaranteeing that a recommendation is universally correct.
- Continuously monitoring repositories in the background.
- Building a full UML or visual architecture modeling application.
- Integrating with every coding assistant during Build Week.

## Target Users

### Primary user

A developer or small engineering team using an AI coding assistant to design and implement a new feature, subsystem, or application.

### Secondary users

- Less-experienced developers learning architectural decision-making.
- Experienced developers who want a consistent architecture workflow.
- Technical leads who want decisions and constraints stored in the repository.
- Teams switching between multiple AI coding assistants.

## High-Level Workflow

```text
Developer requirements
        |
        v
Host coding assistant
running the AI Software Architect role
        |
        +-- Read project context and existing decisions
        +-- Identify architectural forces and ambiguity
        +-- Ask focused clarification questions
        +-- Compare viable architectural options
        +-- Recommend an approach with trade-offs
        +-- Record decisions and constraints
        |
        v
Architecture artifacts in the repository
        |
        v
Coding assistant implements the accepted plan
        |
        v
AI Software Architect reviews conformance on request
        |
        v
Decisions are confirmed, revised, or superseded
```

## User Experience

### Initial analysis

The user invokes AI Software Architect before implementation and provides requirements directly or points it to an existing specification.

The agent reads only relevant context, asks a small number of high-value questions, and presents:

- the interpreted problem;
- architectural forces and quality attributes;
- two or more viable options when alternatives genuinely exist;
- a recommendation;
- rejected or deferred alternatives;
- risks and assumptions;
- decisions requiring user approval.

### Decision approval

The agent does not silently treat every recommendation as final. It presents material decisions for approval, records accepted decisions, and labels unresolved questions.

### Coding handoff

After approval, the agent creates an implementation brief that another coding-agent task can follow without redoing the architecture analysis.

### Conformance review

When requested, the agent compares selected code, a change set, or the repository structure with the recorded architecture contract. Findings distinguish between:

- confirmed violations;
- possible drift requiring review;
- acceptable deviations;
- decisions that should be updated because requirements changed.

## System Architecture

```text
Canonical shared source
|
+-- Agent Skills
+-- Architecture references
+-- Schemas
+-- Templates
+-- Evaluation scenarios
|
+-- Platform packaging
    +-- Codex adapter
    +-- GitHub Copilot adapter
    +-- Claude Code adapter
    +-- Antigravity adapter

At runtime:

User's coding assistant
        |
        +-- platform-specific agent profile or orchestration skill
        +-- shared modular skills
        +-- native repository and shell tools
        +-- optional local deterministic MCP tools
        |
        v
Repository-based architecture artifacts
```

## Canonical Shared Source

"Canonical" means that the project maintains one authoritative version of shared knowledge and contracts. Platform packages are generated from that source rather than maintained as independent copies.

Planned source organization:

```text
shared/
    skills/
        conduct-architecture-interview/
        evaluate-architecture-options/
        create-architecture-decisions/
        prepare-coding-handoff/
        review-architecture-conformance/
    references/
        design-patterns/
        application-architecture/
        distributed-systems/
        domain-driven-design/
        ai-agent-architecture/
    schemas/
    templates/
    evaluations/

adapters/
    codex/
    github-copilot/
    claude-code/
    antigravity/
```

Packaging scripts copy or transform the canonical materials into the directory and manifest format required by each assistant.

## Agent and Skill Responsibilities

### Platform agent adapter

The platform adapter defines:

- how the AI Architect is selected or invoked;
- its role, scope, and high-level instructions;
- which native tools it may use;
- which shared skills it can load;
- platform-specific installation and permission behavior.

### Orchestration skill

Where a platform cannot conveniently package a native custom-agent profile, an orchestration skill can make the active coding-assistant session perform the AI Architect workflow.

This is the expected first approach for the Codex plugin unless native custom-agent packaging becomes suitable during implementation.

### Modular workflow skills

Workflow skills define repeatable activities:

- conducting an architectural interview;
- identifying forces and quality attributes;
- comparing alternatives;
- creating ADRs;
- preparing a coding handoff;
- reviewing architecture conformance.

### Knowledge references

Patterns and architecture styles are primarily reference knowledge loaded by the workflow skills. They are not separate user-facing skills unless they represent a genuinely independent workflow.

The agent should decide whether Strategy, Observer, CQRS, Hexagonal Architecture, or no named pattern is appropriate. The user should not need to select the pattern first.

## Repository Artifact Model

The default project state is stored under `.ai-architect/`:

```text
.ai-architect/
    project-context.md
    architecture-contract.yaml
    decisions/
        ADR-001-example.md
    implementation-plan.md
    constraints/
        architectural-boundaries.yaml
    reviews/
        architecture-review-YYYY-MM-DD.md
```

### `project-context.md`

Contains the problem definition, relevant requirements, stakeholders, constraints, assumptions, and quality attributes.

### `architecture-contract.yaml`

Provides a stable machine-readable summary of accepted architecture decisions. Planned fields include:

- contract version;
- system or feature scope;
- selected architectural style;
- components and responsibilities;
- dependency rules;
- data ownership;
- integration boundaries;
- required patterns;
- prohibited or discouraged approaches;
- quality-attribute priorities;
- linked ADR identifiers;
- unresolved decisions.

### ADRs

Each material decision records:

- status;
- context;
- decision drivers;
- considered options;
- decision;
- positive and negative consequences;
- assumptions;
- validation criteria;
- superseded decisions.

### `implementation-plan.md`

Translates accepted decisions into a coding-agent-ready sequence of milestones, constraints, verification steps, and explicit non-goals.

### Architecture reviews

Reviews contain evidence-linked findings rather than an unexplained score. Each finding identifies the relevant decision or constraint and distinguishes confirmed violations from uncertain observations.

## Platform Strategy

### Codex: first implementation target

The first release is an installable Codex plugin containing:

- an architecture orchestration skill;
- modular architecture workflow skills;
- references, schemas, and templates;
- plugin metadata and local installation support;
- optional hooks or local MCP configuration only if required by validated functionality.

The user runs the architect with the selected Codex model and Codex credits. The plugin itself makes no model API calls.

### Claude Code

A later Claude Code plugin can bundle:

- a native custom-agent profile;
- the shared `SKILL.md` skills;
- templates and schemas;
- optional local hooks or MCP configuration.

### GitHub Copilot

A later Copilot plugin can bundle:

- a native custom-agent profile;
- the shared skills;
- repository instructions where needed;
- optional hooks or MCP configuration.

### Google Antigravity

The initial Antigravity adapter can provide:

- Agent Skills in the supported project or user scope;
- a workflow or rule that activates the AI Architect role;
- shared templates and schemas;
- optional local MCP tools.

Native Antigravity SDK integration is a possible later enhancement, not a first-version requirement.

### Other coding assistants

Other adapters may use native agent profiles, Agent Skills, rules, commands, extensions, or MCP depending on the host. Support is added only after the platform's extension model has been validated.

## Optional Local MCP Design

A local STDIO MCP server should be introduced only when it provides clear deterministic value.

Potential tools include:

- validate an architecture contract against its schema;
- build and query a dependency graph;
- detect forbidden module dependencies;
- query and link ADRs;
- compare declared boundaries with repository structure;
- calculate architecture metrics;
- integrate a static-analysis tool;
- return machine-readable conformance evidence.

The coding assistant remains responsible for interpretation and recommendations. MCP tools return evidence and deterministic results.

## Security and Privacy

- Project analysis remains local unless the user's coding assistant has different documented behavior.
- The project does not operate a telemetry or data-collection backend.
- No model-provider credentials are requested or stored by AI Software Architect.
- Optional integration credentials must be read through host-supported secrets or environment variables.
- Secrets must never be written to `.ai-architect/`.
- Destructive repository actions require the host's normal permission and approval flow.
- Generated architecture recommendations are advisory and must identify significant uncertainty.

## How This Differs From Existing Skills

Many architecture-related skills explain a known pattern, generate an implementation, or review an existing codebase.

A typical documentation-oriented workflow is:

```text
Developer selects Strategy Pattern
        |
        v
Assistant loads Strategy documentation
        |
        v
Assistant generates a Strategy implementation
```

This assumes that the developer already knows which pattern is appropriate.

AI Software Architect addresses the earlier reasoning problem:

> Which architectural solution, if any, best fits these requirements and constraints?

It may recommend Strategy, Factory Method, Observer, Repository, CQRS, Hexagonal Architecture, or no named pattern. It must explain alternatives and consequences rather than treating pattern usage as the goal.

## Key Differentiator

Existing knowledge skills commonly answer:

> Tell me about Strategy.

AI Software Architect answers:

> Your requirements indicate interchangeable behaviors with different operational constraints. Strategy is one viable option. Here are the alternatives, trade-offs, assumptions, and the decision we should record before implementation.

The innovation is a repeatable, repository-persistent architectural decision workflow that operates inside the developer's chosen coding assistant.

## Preliminary Research

An initial review considered public skill marketplaces and directories including:

- skills.sh;
- SkillsMP;
- Skills Directory;
- Agent Registry.

Architecture-related skills were found for areas such as Clean Architecture, Hexagonal Architecture, Domain-Driven Design, design patterns, refactoring, and codebase improvement.

The initial review did not identify a directly comparable, assistant-portable workflow that combines pre-implementation architectural analysis, explicit alternative comparison, repository-persistent decisions, coding handoff, and later conformance review.

This research is preliminary rather than exhaustive. Claims about uniqueness must be revalidated before publication or submission.

## Example Conversation

User:

> I need a payment platform that supports Stripe, PayPal, and future providers.

AI Software Architect:

> I identified two important forces: payment providers implement interchangeable behavior, and future providers may be introduced independently. Before recommending an architecture, will third parties be allowed to add providers, and must payment processing be synchronous?

User:

> Third parties may add providers later. Initial processing is synchronous, but callbacks are asynchronous.

AI Software Architect:

> I recommend a provider port with Strategy implementations and dependency injection. A registry is preferable to hard-coded factory branching because third-party discovery is a stated requirement. Callback processing introduces separate idempotency and delivery concerns; it should not be hidden inside the provider-selection pattern. I will record these as separate decisions and define their consequences.

After approval, the agent creates ADRs, an architecture contract, and a coding handoff. The coding assistant can then implement the accepted design.

## Build Week MVP

### Required capabilities

The first Codex plugin must demonstrate one complete architecture-first loop:

1. Install and activate the plugin locally.
2. Analyze a project or feature specification.
3. Ask focused clarification questions.
4. Identify architectural forces and quality attributes.
5. Compare at least two credible options when alternatives exist.
6. Recommend an approach with explicit trade-offs and uncertainty.
7. Generate at least one ADR.
8. Generate `architecture-contract.yaml`.
9. Generate a Codex-ready implementation plan.
10. Review a small implementation or proposed file structure against the recorded decisions.

### Initial knowledge scope

The MVP should cover a deliberately limited but useful set of concepts:

- modular monolith and service-oriented alternatives;
- layered, clean, and hexagonal architecture;
- dependency inversion and ports/adapters;
- Strategy, Factory Method, Observer, Adapter, Command, and Repository;
- basic event-driven integration;
- idempotency, transactional outbox, and retry concerns;
- explicit recommendation of no pattern when appropriate.

### Demonstration scenario

The demo should show:

1. A requirement that appears easy to implement immediately.
2. The architect discovering a meaningful ambiguity or quality constraint.
3. A comparison of plausible alternatives.
4. An accepted decision recorded in the repository.
5. Codex implementing or planning from the architecture contract.
6. The architect identifying either a deliberate conformance result or a seeded deviation.

## Evaluation Strategy

The project should be evaluated against repeatable scenarios rather than subjective impressions alone.

For each scenario, compare:

- a general coding-assistant request without AI Software Architect;
- the same request using the architecture workflow.

Evaluation dimensions include:

- requirement coverage;
- relevance of clarification questions;
- quality of identified architectural forces;
- credibility of alternatives;
- correctness and specificity of trade-offs;
- avoidance of unnecessary patterns;
- consistency between decisions and implementation handoff;
- ability to identify architecture drift;
- usefulness and readability of generated artifacts.

The evaluation does not require different assistants to produce identical recommendations. It checks whether each result follows the declared method and produces evidence-supported, internally consistent decisions.

## Future Capabilities

- Broader GoF and enterprise pattern knowledge
- Domain-Driven Design and bounded-context analysis
- Event sourcing and CQRS guidance
- Cloud-native and distributed-systems knowledge
- AI agent architecture patterns
- Framework- and language-specific references
- Dependency-graph and boundary validation
- Architecture drift detection
- Pull-request architecture review
- CI integration using deterministic local tooling
- UML and diagram generation
- Technical-debt evidence and trend analysis
- Additional coding-assistant adapters

## Long-Term Vision

AI Software Architect should evolve into an open, portable architectural method for agentic software development.

It should remain:

- model-independent at the product level;
- compatible with multiple coding assistants;
- local-first and user-controlled;
- explicit about assumptions and uncertainty;
- extensible through modular skills;
- grounded in version-controlled architectural decisions;
- useful to both developers and coding agents.

## Mission

Create an AI Software Architect that reasons like an experienced software architect, works inside the coding assistant a developer already uses, and makes architecture a first-class, persistent part of AI-assisted development rather than an afterthought.

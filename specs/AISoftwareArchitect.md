# AI Software Architect

## Vision

AI Software Architect is an autonomous architectural reasoning agent that collaborates with AI coding assistants (such as Codex, Claude Code, Antigravity, and future agentic IDEs) to make architectural decisions **before** code is generated.

Instead of simply generating code or explaining design patterns, the agent acts like an experienced software architect. It analyzes project requirements, identifies architectural challenges, recommends the most appropriate design patterns and architectural styles, explains the trade-offs behind each recommendation, asks clarifying questions when necessary, and guides the coding agent throughout implementation.

The goal is to move AI-assisted software development from **code generation** to **architecture-driven development**.

---

# Problem Statement

Current AI coding assistants are excellent at writing code, but they rarely make explicit architectural decisions.

For example, if a user asks an AI assistant to build a notification system, it will typically generate working code immediately. However, it usually does not stop to reason about whether the problem naturally fits the Observer pattern, Strategy pattern, Factory Method, or another architectural solution.

Similarly, today's AI assistants rarely explain:

* why a design pattern should be chosen,
* what alternatives exist,
* the trade-offs between different approaches,
* or whether the generated implementation still conforms to the selected architecture.

These architectural decisions remain largely implicit.

---

# Our Solution

The AI Software Architect becomes the first agent involved in a software project.

Instead of immediately generating code, it performs architectural analysis.

Typical workflow:

1. Analyze project requirements.
2. Identify architectural challenges.
3. Recommend one or more design patterns or architectural styles.
4. Explain the reasoning behind every recommendation.
5. Ask clarifying questions when requirements are ambiguous.
6. Generate an Architecture Decision Report.
7. Hand over the architectural plan to the coding agent.
8. Continue validating implementation throughout development.

This creates a collaborative workflow between an architectural reasoning agent and one or more coding agents.

---

# High-Level Workflow

```text
User Requirements
        │
        ▼
AI Software Architect
        │
        ├── Analyze requirements
        ├── Detect architectural problems
        ├── Recommend patterns
        ├── Explain trade-offs
        ├── Ask clarifying questions
        └── Produce Architecture Report
                 │
                 ▼
AI Coding Assistant
(Codex / Claude Code / Antigravity / etc.)
                 │
        Implements architecture
                 │
                 ▼
AI Software Architect
        Reviews implementation
        Detects deviations
        Suggests improvements
```

---

# How This Differs From Existing Skills

Current design pattern skills generally provide documentation or implementation guidance.

Typical workflow today:

Need Strategy Pattern

↓

Load Strategy Skill

↓

Read documentation

↓

Generate Strategy implementation

This assumes the developer already knows which pattern should be used.

Our project solves a much earlier and more difficult problem:

**Which architectural solution is the most appropriate for this problem?**

Instead of teaching a pattern, the AI reasons about the software problem itself.

It may recommend:

* Strategy
* Factory Method
* Builder
* Observer
* Repository
* CQRS
* Clean Architecture
* Hexagonal Architecture

or explain why no pattern should be used at all.

The innovation is architectural reasoning rather than architectural documentation.

---

# Research Performed

We explored several public AI skill marketplaces to determine whether similar solutions already exist.

Platforms investigated included:

* skills.sh
* Skills Directory
* SkillsMP
* Agent Registry

## Findings

### skills.sh

The largest public skills repository contains hundreds of thousands of skills.

Relevant findings included:

* Architecture-related skills
* Clean Architecture
* Hexagonal Architecture
* Domain Driven Design
* Codebase architecture improvement

These skills primarily explain architectural concepts or help improve existing codebases.

We did not find an agent that performs architectural reasoning before implementation.

---

### SkillsMP

SkillsMP indexes millions of SKILL.md files.

Most development-related skills focus on:

* UI development
* React
* Code review
* Documentation
* Testing
* General engineering workflows

No architectural reasoning agent was identified.

---

### Skills Directory

The platform contains many software engineering skills, including:

* Refactoring
* Debugging
* API Design
* Documentation
* Testing

Again, no solution focused on selecting the best design pattern or architectural approach based on project requirements.

---

### Agent Registry

Agent Registry provides tooling for publishing and consuming skills.

No comparable AI Software Architect was found.

---

### Closest Existing Skill

The closest match we found is a Design Patterns Skill.

Its purpose is essentially:

* identify design patterns
* explain them
* implement them
* detect anti-patterns

While useful, it still assumes the developer already knows which design pattern they are looking for.

This is fundamentally different from our vision.

---

# Key Differentiator

Current skills answer:

> "Tell me about Strategy."

AI Software Architect answers:

> "Based on your requirements, Strategy is probably the best solution. Here is why. Here are two alternatives. Here are the trade-offs."

This moves architectural expertise from passive documentation into active decision making.

---

# Knowledge Architecture

Rather than embedding every design pattern into the agent's prompt, architectural knowledge is organized as modular skills.

Example:

```text
skills/

    gof/
        strategy/
        observer/
        builder/
        decorator/
        adapter/
        command/

    architecture/
        clean-architecture/
        ddd/
        cqrs/
        repository/
        hexagonal/

    cloud/
        saga/
        circuit-breaker/
        outbox/
        bulkhead/

    ai/
        planner-agent/
        reflection-agent/
        multi-agent/
```

The AI Software Architect dynamically loads only the knowledge required for the current project.

---

# Long-Term Vision

The project should evolve beyond the original Gang of Four patterns.

Eventually the knowledge base should include:

* GoF Design Patterns
* Enterprise Patterns
* Clean Architecture
* Domain Driven Design
* CQRS
* Event Sourcing
* Microservices
* Cloud-native architecture
* Distributed systems
* AI agent design patterns
* Language-specific best practices
* Framework-specific architecture guidance

The AI becomes a universal architectural advisor rather than a design pattern encyclopedia.

---

# Example Conversation

User:

"I need a payment platform that supports Stripe, PayPal and future providers."

AI Software Architect:

"I detected multiple interchangeable payment providers."

"I recommend the Strategy Pattern because each provider implements the same payment interface."

"Since providers may be created dynamically, I also recommend Factory Method."

"Will new payment providers be added by third parties in the future?"

User:

"Yes."

Architect:

"In that case, Dependency Injection and plugin discovery should also be considered."

Only after these architectural decisions are finalized does the coding agent begin implementation.

---

# Why This Has Strong Potential

We believe the opportunity lies in a gap that current AI coding assistants do not address.

Today's tools excel at generating code, but architectural reasoning is still largely left to the developer.

AI Software Architect fills that gap by:

* thinking before coding begins,
* making explicit architectural decisions,
* documenting architectural rationale,
* reducing poor design decisions early,
* improving maintainability,
* improving scalability,
* helping less experienced developers learn architectural thinking,
* and collaborating with coding agents instead of replacing them.

This also aligns naturally with the evolution of agentic software development, where specialized AI agents cooperate to solve different parts of the software lifecycle.

---

# Future Features

Possible future capabilities include:

* Interactive architectural interviews
* Architecture Decision Records (ADR) generation
* UML generation
* Architecture validation during development
* Automatic refactoring recommendations
* Detection of anti-patterns
* Continuous architecture quality scoring
* Technical debt estimation
* Architecture drift detection
* Framework-specific recommendations
* Multi-language implementations
* Integration with GitHub pull requests
* Integration with CI/CD pipelines
* Integration with AI coding assistants through Skills

---

# Mission

Create an AI Software Architect that reasons like an experienced software architect, collaborates with AI coding assistants, and helps developers build better software by making architecture a first-class part of AI-assisted software development rather than an afterthought.

---
name: create-architecture-decisions
description: Present architecture recommendations for approval and create validated ADRs and architecture contracts. Use after credible options have been compared or when an existing material architecture decision must be proposed, accepted, rejected, revised, or superseded.
license: MIT
---
<!--
SPDX-FileCopyrightText: 2026 Leonardo Muffato (AUTOSOFT Engineering - www.autosoft-engineering.de)
SPDX-License-Identifier: MIT
-->

# Create Architecture Decisions

1. Present the recommendation, drivers, trade-offs, uncertainty, alternatives, and validation criteria.
2. Ask the user to approve, revise, or provide more information. Do not infer approval from silence.
3. Assign stable `OPT-NNN` and `ADR-NNN` identifiers without reusing identifiers.
4. After approval and before drafting, load the exact bundled ADR template, contract example, ADR-authoring reference, and implementation-plan template. A host adapter may provide these four canonical sources as one generated bundle; when it does, load that bundle once instead of reading the sources separately. Treat their nested object shapes as authoritative and never infer list-item shapes from field names or model memory. The contract example demonstrates all dependency policies: `allow-via-interface` requires `via_interface`, while `allow` and `deny` must omit it. Then create schema-valid ADR frontmatter and an `architecture-contract.yaml` whose references resolve to accepted ADRs and declared components.
5. Submit complete candidates to the active host adapter's deterministic pre-write
   validation. In Codex, the trusted `PreToolUse` hook reconstructs the proposal,
   validates the complete `ArchitectureArtifactBundle`, and scans every generated
   artifact before the write. The `PostToolUse` hook verifies that the persisted
   bundle matches the validated candidates. A denied or unavailable validation must
   never be reported as success.
6. Strip the source-template SPDX comment from user-owned generated artifacts.
7. Follow the orchestration skill's concurrent-edit and atomic multi-file update protocol.

## Resources

- Load [ADR authoring](references/adr-authoring.md) whenever creating or superseding an ADR.
- Use the [ADR template](assets/adr-template.md) to render a decision; remove its SPDX source header from generated output.
- Load the [contract example](assets/architecture-contract.example.yaml) before every contract draft. It intentionally demonstrates the nested shapes and every dependency-policy variant; preserve those shapes while replacing example values, then validate the contract and complete artifact bundle against the canonical Pydantic models.

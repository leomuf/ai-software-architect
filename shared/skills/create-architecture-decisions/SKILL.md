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
4. After approval, create schema-valid ADR frontmatter and an `architecture-contract.yaml` whose references resolve to accepted ADRs and declared components.
5. Run `validate_complete_architecture_contract` with
   `validation_scope: complete-candidate-contract`, inspect `result.valid`, and run
   `scan_generated_architecture_artifact` before proposing writes. An invalid result
   is a failed validation, even when the MCP transport call itself completed.
6. Strip the source-template SPDX comment from user-owned generated artifacts.
7. Follow the orchestration skill's concurrent-edit and atomic multi-file update protocol.

## Resources

- Load [ADR authoring](references/adr-authoring.md) whenever creating or superseding an ADR.
- Use the [ADR template](assets/adr-template.md) to render a decision; remove its SPDX source header from generated output.
- Use the [contract example](assets/architecture-contract.example.yaml) as shape guidance; validate against the canonical Pydantic model rather than copying values.

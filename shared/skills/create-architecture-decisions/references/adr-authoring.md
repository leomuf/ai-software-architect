<!--
SPDX-FileCopyrightText: 2026 Leonardo Muffato (AUTOSOFT Engineering - www.autosoft-engineering.de)
SPDX-License-Identifier: MIT
-->

# ADR Authoring

Record one material decision per ADR. State the context and forces that existed when deciding, enumerate credible options by stable identifiers, name the selected option, and capture positive and negative consequences without promotional language.

Use `proposed` before approval and `accepted` only after explicit approval. Never edit historical meaning invisibly: supersede an accepted decision with a new ADR and link both records. Make validation criteria observable. Keep confidential values and source excerpts out of the record.

The file begins with safe YAML frontmatter conforming to `ArchitectureDecisionArtifact`. The filename starts with the matching `ADR-NNN`; any slug uses lowercase ASCII letters, digits, and single hyphens. The Markdown body is a deterministic rendering of the same fields.


<!--
SPDX-FileCopyrightText: 2026 Leonardo Muffato (AUTOSOFT Engineering - www.autosoft-engineering.de)
SPDX-License-Identifier: MIT
-->

# Finding Classification

- **Confirmed violation:** reliable evidence directly contradicts an accepted rule. Cite the evidence and rule.
- **Possible drift:** evidence is incomplete, ambiguous, dynamically resolved, or suggests a mismatch requiring human review.
- **Acceptable deviation:** implementation differs but remains permitted by the decision or has separately approved justification.

Severity measures likely architectural impact: `critical` for immediate systemic or security harm, `high` for a major boundary or quality breach, `medium` for material localized drift, `low` for limited maintainability risk, and `info` for observations. Confidence measures evidence strength, not impact. State tool limitations and never upgrade confidence to compensate for severity.


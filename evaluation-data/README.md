<!--
SPDX-FileCopyrightText: 2026 Leonardo Muffato (AUTOSOFT Engineering - www.autosoft-engineering.de)
SPDX-License-Identifier: MIT
-->

# Exploratory Evaluation Performance Data

`exploratory-runs.jsonl` is the canonical, append-only performance history for
eligible exploratory tests. Each non-empty line must validate against
`exploratory-performance.schema.yaml` and the strict Pydantic contract in
`adapters/codex/evaluations/performance_models.py`.

Missing phases use JSON `null`; they are never represented as zero or `NaN`.
Aborted, cancelled, setup-failed, and infrastructure-failed tasks do not enter the
canonical ledger. Codex-assisted historical classifications and their exclusion
reasons are retained separately under `imports/`.

Do not store prompts, full responses, hidden reasoning, credentials, or sensitive
absolute paths in this directory.

## Contents

- `exploratory-runs.jsonl` is the canonical ledger. It contains the approved
  historical Desktop observations and eligible earlier runner reports.
- `exploratory-performance.schema.yaml` is the portable YAML representation of the
  canonical record contract.
- `historical-import-overrides.yaml` records evidence-backed metadata corrections
  for older runner reports.
- `imports/codex-desktop-history-review.json` records the Codex-assisted semantic
  review, including interrupted tasks that were excluded.
- `imports/existing-runner-reports-import.json` records accepted and rejected
  historical `report.json` inputs. Paths are repository-relative.

Generated Markdown, CSV, and JSON views belong below `.tmp/evaluations/`; they are
reproducible and are not versioned.

## Updating the history

The non-interactive Python runner appends eligible observations automatically after
each real campaign. Dry runs and phases that did not produce a usable response are
not appended.

Interactive Desktop campaigns require an explicit post-run review because
timestamps alone cannot establish semantic eligibility. Export candidate tasks,
create a review draft, let Codex or a human review the bounded evidence, and apply
only the approved batch. The commands are documented in
[`../scripts/README.md`](../scripts/README.md#maintain-exploratory-performance-history).

Render the complete reusable history with:

```powershell
.\scripts\show-exploratory-performance.ps1
```

The same renderer feeds the GitHub Actions Job Summary and uploads Markdown, CSV,
and JSON views as a CI artifact. CI reads the ledger but never mutates it.

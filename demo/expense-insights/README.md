<!--
SPDX-FileCopyrightText: 2026 Leonardo Muffato (AUTOSOFT Engineering - www.autosoft-engineering.de)
SPDX-License-Identifier: MIT
-->

# Expense Insights Demo Project

This deliberately small application is the reproducible end-to-end demo target
for AI Software Architect. It imports transactions, assigns categories, and
prints a monthly summary. The implementation works, but input, business policy,
reporting, and command-line concerns are concentrated in one Python module.

The demo asks the architect to make those boundaries explicit before a coding
agent begins a larger refactor.

## Product Constraints

- The application remains a local, single-user desktop tool for at least one
  year.
- It must support both a command-line interface and a desktop interface.
- CSV import works today; OFX and bank-specific formats are expected later.
- Categorization rules change frequently and must be independently testable.
- Reports may eventually be exported to CSV and rendered as charts.
- A cloud service, distributed architecture, database, and plugin framework
  would be unnecessary for the expected scale.
- Normal workloads contain fewer than 5,000 transactions.
- The first architectural change should be incremental and preserve current
  behavior.

## Run the Sample

The sample uses only the Python standard library:

```powershell
python expense_insights.py sample-transactions.csv
```

Running the sample is optional for the architecture workflow. The architect
reviews source statically and must not execute analyzed application code.

## Run the Architecture Demo

1. Install AI Software Architect and activate its reviewed hooks.
2. In Codex, create a project or task whose selected folder is this
   `demo/expense-insights/` directory.
3. Select **GPT-5.6 Sol** with **Medium** reasoning.
4. Use the three prompts in [`DEMO_PROMPTS.md`](DEMO_PROMPTS.md).
5. After recording or testing, run
   [`reset-demo.ps1`](reset-demo.ps1) from an ordinary PowerShell terminal to
   remove only generated `.ai-architect/` artifacts.

If PowerShell reports that script execution is disabled, review the script and
follow the user-scoped `RemoteSigned` or temporary process-scoped instructions in
the repository's
[`scripts/README.md`](../../scripts/README.md#powershell-execution-policy).

The exact recommendation and prose may vary because GPT-5.6 performs the
reasoning. A successful run consistently demonstrates:

- a comparison of credible alternatives for one architecture decision;
- explicit user approval before recording the decision;
- durable ADR, contract, context, and coding-handoff artifacts;
- no changes to `expense_insights.py`; and
- a read-only conformance review tied to the accepted decision.

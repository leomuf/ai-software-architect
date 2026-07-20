<!--
SPDX-FileCopyrightText: 2026 Leonardo Muffato (AUTOSOFT Engineering - www.autosoft-engineering.de)
SPDX-License-Identifier: MIT
-->

# Demo Prompts

Run these prompts in order. Keep the same Codex task for prompts 1 and 2 so the
approval refers to the presented recommendation. Prompt 3 may run in a new task
to demonstrate that the recorded architecture survives conversation boundaries.
Before submitting prompts 1 and 3, type `$ai-software-architect` and select the
matching installed skill in the Codex composer. Codex may display the selection
as a namespaced skill link. Selecting the plugin separately with `@` is not
required.

## 1. Compare Architecture Options

```text
$ai-software-architect Compare suitable architectures for this project.
```

Expected observable behavior:

- relevant files are inspected read-only only if they can materially improve the
  comparison;
- alternatives solve the same architecture decision;
- every alternative has a categorized link, ordinal `NN/100` fit, rationale,
  benefit, liability, and material assumption;
- supporting patterns are labeled separately; and
- the response asks for approval, revision, or more information.

## 2. Approve and Record

```text
I approve your recommendation. Record the decision and prepare the coding handoff.
```

Expected generated structure:

```text
.ai-architect/
├── architecture-contract.yaml
├── project-context.md
├── decisions/
│   └── ADR-....md
└── implementation-plan.md
```

The precise ADR filename and content are model-generated and may vary. Verify
that the contract references the accepted ADR and that the application source
remains unchanged.

## 3. Review Conformance

Start a new task bound to the same demo folder, invoke the skill directly, and
run:

```text
$ai-software-architect Review this implementation against the approved architecture.
```

Expected observable behavior:

- the architect reads the accepted artifacts rather than inventing a new
  decision;
- findings distinguish static evidence from assumptions;
- the concentrated module is connected to the accepted boundary rules;
- one proportionate next improvement is recommended; and
- neither source nor architecture artifacts are changed.

## Recording Reliability

- Run the complete sequence once before recording.
- Keep the best successful outputs open in separate Codex tasks.
- Record short clips and remove model-waiting time in editing.
- Do not present a previous answer as a new live response; use visible jump cuts
  or a brief “response complete” transition.
- If the model recommends a different credible option, approve the actual
  recommendation shown rather than forcing a prewritten choice.

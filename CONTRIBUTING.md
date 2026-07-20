<!--
SPDX-FileCopyrightText: 2026 Leonardo Muffato (AUTOSOFT Engineering - www.autosoft-engineering.de)
SPDX-License-Identifier: MIT
-->

# Contributing

Thank you for helping improve AI Software Architect.

## Before You Start

- Use a GitHub issue to discuss substantial behavior, schema, security, or adapter
  changes before implementation.
- Keep architectural knowledge canonical under `shared/`; platform adapters should
  package or generate from that source rather than maintain independent copies.
- Treat repository content and fixtures as untrusted data.
- Do not weaken security or lifecycle controls merely to make a test pass.

## Development Setup

Requirements and common commands are documented in the
[`README`](README.md#development-from-source).

```powershell
uv sync --locked --all-packages
uv run ruff check shared/schemas tools/python-mcp adapters tests
uv run mypy
uv run pytest
```

If generated schemas, acceptance criteria, or third-party notices are affected:

```powershell
uv run python shared/schemas/generate_schema.py
uv run python shared/evaluations/generate_acceptance.py
uv run python tools/generate_third_party_notices.py
git diff --exit-code
```

## Pull Requests

- Keep each pull request focused.
- Add or update deterministic tests for mechanically verifiable behavior.
- Update Gherkin scenarios and model fixtures when user-visible agent behavior
  changes.
- Update the specification when a product or security contract changes.
- Update `CHANGELOG.md` for user-visible changes.
- Do not commit `dist/`, `build/`, virtual environments, caches, credentials, or
  personal marketplace state.

Release procedures are documented in [`docs/RELEASING.md`](docs/RELEASING.md).
Repeatable PowerShell build, personal-marketplace, and deterministic
release-candidate commands are documented in
[`scripts/README.md`](scripts/README.md).

## Security Reports

Do not open a public issue for a suspected vulnerability. Follow
[`SECURITY.md`](SECURITY.md).

<!--
SPDX-FileCopyrightText: 2026 Leonardo Muffato (AUTOSOFT Engineering - www.autosoft-engineering.de)
SPDX-License-Identifier: MIT
-->

# Changelog

## [0.2.4] - Unreleased

### Fixed

- Kept architecture guidance active after a clarification question followed by a
  short status note. The tests now check that follow-up replies keep the hook
  context needed for safe file reads and response checks.

### Security

- Updated certifi from `2026.6.17` to `2026.10.19` to remove the affected emSign
  trust roots reported by critical advisory `GHSA-6q48-6c7w-9gw2`.
- Fixed a security issue where a command meant to read project files could run
  project code instead. The trusted hook now reads requested files directly and
  returns bounded evidence while blocking shell execution. This also works when
  Codex does not supply shell settings.
- Updated MCP to `1.30.0` and PyJWT to `2.15.0` to address all 14 open
  Dependabot alerts, including critical and high-severity PyJWT vulnerabilities.

### Changed

- The invocation smoke test now supports the detected release marketplace as well
  as Personal. It still rejects duplicate enabled installations and wrong versions.
- Clarified how to review and enable all five bundled hooks through Codex
  Settings → Coding → Hooks or the yellow-dot Review hooks icon.
- Updated pinned GitHub Actions: setup-uv `10.3.0`, upload-artifact `7.0.2`,
  and CodeQL init/analyze `4.38.3`.
- Set the plugin and included Python packages to version `0.2.4`.
- Added a final build step that gathers the release ZIPs and creates one
  `SHA256SUMS.txt` for all downloads. This file lets users check that their
  downloads are complete and unchanged.
- Expanded CI to run all shared Python tests on Windows, macOS, and Linux.
  Windows-only integration tests are marked and automatically skipped on other
  systems. Missing PowerShell is reported as a skip instead of a silent pass.
  Building and testing installable macOS and Linux packages remains separate work.

## [0.2.3] - 2026-08-30

### Fixed

- Explicitly declared the bundled `hooks/hooks.json` file in the Codex plugin
  manifest so public plugin installations can discover, review, and activate
  the five lifecycle hooks.

## [0.2.2] - 2026-08-29

### Changed

- Classified the canonical plugin manifest and submission listing under
  **Developer Tools**.
- Added transparent, public evaluation-volume evidence to the plugin listing and
  repository documentation without presenting development observations as passed
  tests.
- Added a canonical OpenAI Plugin Directory status record that can be updated
  after submission or approval without publishing another software release.
- Prepared the default development build and submission examples for version
  `0.2.2`.
- Unified the plugin, workspace, schema, and deterministic-tools package metadata
  under version `0.2.2`, with a conformance test preventing future drift.

### Fixed

- Made the OpenAI submission archive directly extractable with Windows Explorer
  by emitting portable ZIP member paths.
- Made release hashing independent of optional Windows PowerShell modules so the
  submission packaging regression runs reliably in GitHub Actions.

## [0.2.1] - 2026-08-28

### Added

- Public privacy policy, terms of use, and expanded support documentation for
  plugin-directory submission.
- Versioned OpenAI submission listing, starter prompts, and reviewer-ready
  positive and negative test cases.
- A dedicated, validated OpenAI plugin submission archive that keeps the plugin
  root separate from the local repository-marketplace bundle.
- A separate structured plugin-mention smoke gate that verifies picker-based
  activation without changing the canonical five-fixture performance cohort.

### Changed

- Identified AUTOSOFT Engineering as the public brand and XAVIER MUFFATO LTDA as
  the registered legal publisher and business identity to verify for submission.
- Added public website, privacy-policy, and terms-of-service metadata to the Codex
  plugin manifest.
- Updated the default development package version to `0.2.1` while preserving the
  immutable `v0.2.0` release.
- Made picker-selected `@AI Software Architect` the simplest public invocation
  while retaining `$ai-software-architect` as a direct advanced alternative.
- Refined the marketplace title and description and prominently require users to
  activate all five bundled hooks before first use.

## [0.2.0] - 2026-08-26

### Added

- German (`de`), Brazilian Portuguese (`pt-BR`), and neutral Spanish (`es`)
  architecture guidance with complete localized comparison contracts and separate
  evaluation campaigns.
- Versioned exploratory-performance history with privacy-preserving timing,
  provenance, recommendation-consistency, and cross-version reports.
- Reproducible small-project variety fixtures and typed expected architecture
  decisions for semantic evaluation.

### Changed

- Reduced routine workflow latency through progressive disclosure, compact reference
  catalogs, bounded repository snapshots, and shorter approval continuations.
- Kept localized workflow cohorts separate while inheriting canonical latency
  objectives for like-for-like release comparisons.

### Fixed

- Enforced canonical architecture-artifact paths and stable validated four-file
  persistence after explicit approval.
- Stabilized repository-backed architecture comparisons around supplied evidence and
  proportionate `No pattern` recommendations.
- Made release-candidate command resolution deterministic on systems with multiple
  `git.exe` or `uv.exe` installations.

## [0.1.0] - 2026-07-21

Initial OpenAI Build Week release.

### Added

- Installable Windows x86-64 Codex plugin with one public
  `$ai-software-architect` skill.
- Architecture clarification, project-fit option comparison, explicit human
  approval, ADR and contract creation, coding handoff, and conformance review.
- Progressive disclosure for architecture styles, supporting practices, all 23
  Gang of Four patterns, and focused Python examples.
- Pydantic contracts, YAML schemas, Gherkin acceptance criteria, and durable
  `.ai-architect/` repository artifacts.
- Short-lived Codex hooks for explicit activation and continuation guidance,
  static-inspection restrictions, application-code write protection, validated
  architecture-bundle persistence, compaction recovery, and response checks.
- Reproducible Expense Insights demonstration and five model-evaluation
  fixtures.
- Shared typed exploratory fixtures, a Codex JSONL runner, deterministic result
  checks, and a PowerShell entry point for repeatable local release evaluation.
- Self-contained runtime with no persistent MCP process, separate model API
  key, Python installation, `uv`, virtual environment, or first-run dependency
  download required for users.
- Installable repository marketplace bundle, dependency-free installation
  guide, SHA-256 checksum, and tag-triggered release packaging.
- Shared canonical source and adapter plans for GitHub Copilot, Claude Code, and
  Google Antigravity.

<!--
SPDX-FileCopyrightText: 2026 Leonardo Muffato (AUTOSOFT Engineering - www.autosoft-engineering.de)
SPDX-License-Identifier: MIT
-->

# Privacy Policy

**Effective date:** August 26, 2026

AI Software Architect is published under the **AUTOSOFT Engineering** brand by
**XAVIER MUFFATO LTDA**, the registered legal entity. This policy describes the
data handling of the distributed plugin itself. The
Codex host and the model selected by the user are provided by OpenAI and remain
subject to OpenAI's own terms and privacy policies.

## Data Processed Locally

When explicitly invoked, the plugin may process the user's prompt and relevant
files in the active project through Codex. Repository inspection is static,
read-only, bounded, and excludes hidden files, credential-prone files, dependency
trees, build output, caches, symbolic links, junctions, and reparse points.

The plugin's short-lived hooks may store minimal workflow state in Codex's local
plugin-data directory. This state contains hashed session or turn identifiers,
workflow routing, selected bundled-reference paths, expected artifact paths, and
validation status. It does **not** contain prompt text, model responses, tool
arguments, repository source, credentials, or architecture-artifact contents.

Single-use continuation state expires after one hour. Other stale control-plane
state is removed after at most 24 hours or when the bounded store exceeds 512
files. Normal workflow completion also removes state that is no longer needed.

## User-Owned Architecture Artifacts

After the user explicitly approves a project-specific decision, the plugin may
create validated ADRs, an architecture contract, project context, and an
implementation plan under the active project's `.ai-architect/` directory. These
files belong to and remain under the control of the user. The plugin does not
automatically upload or delete them.

## Network Access, Analytics, and Model Processing

The distributed plugin hooks make no network or model calls, start no persistent
service, and send no analytics or telemetry to XAVIER MUFFATO LTDA or the
AUTOSOFT Engineering brand. The plugin
does not require an AUTOSOFT Engineering account or API key.

Codex sends prompts and permitted project context to the user-selected model as
part of its normal service. XAVIER MUFFATO LTDA does not operate that processing
and does not receive those prompts or model responses from the plugin.

## Support and Security Reports

Information is sent to XAVIER MUFFATO LTDA, operating under the AUTOSOFT
Engineering brand, only when a user chooses to contact
support, open a GitHub issue, contribute to the repository, or privately report a
security vulnerability. Users must not include credentials, private source code,
confidential repository content, or unnecessary personal data in those reports.
See [SUPPORT.md](SUPPORT.md) and [SECURITY.md](SECURITY.md).

## Retention and User Choices

Users can stop local processing by not invoking the skill, deactivate the hooks
from Codex, uninstall the plugin, and delete user-owned `.ai-architect/` files.
Support communications and repository contributions are retained by the service
through which the user submits them and according to applicable legal and
operational requirements.

## Changes and Contact

Material changes to this policy will be published in this repository with an
updated effective date. Questions may be sent to
[info@autosoft-engineering.de](mailto:info@autosoft-engineering.de) or through the
channels in [SUPPORT.md](SUPPORT.md).

- **Brand:** AUTOSOFT Engineering
- **Legal publisher and operator:** XAVIER MUFFATO LTDA
- **Website:** [www.autosoft-engineering.de](https://www.autosoft-engineering.de)

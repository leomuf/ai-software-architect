<!--
SPDX-FileCopyrightText: 2026 Leonardo Muffato (AUTOSOFT Engineering - www.autosoft-engineering.de)
SPDX-License-Identifier: MIT
-->

# OpenAI Plugin Directory Status

This page is the canonical public status record for the AI Software Architect
submission to the OpenAI Plugin Directory. Submission and approval are
distribution events, not software changes, so this page can be updated through a
documentation-only pull request without publishing another GitHub Release.

## Current Status

| Field | Value |
| --- | --- |
| Status | **Available in the public marketplace — maintainer confirmed** |
| Plugin version | `0.2.3` |
| Publisher brand | AUTOSOFT Engineering |
| Verified legal publisher | XAVIER MUFFATO LTDA |
| Availability confirmed by maintainer | 2026-10-26 |
| Submission date | Not recorded here |
| Approval date | Not recorded here |
| Public directory URL | Not recorded here; find AI Software Architect in the public marketplace |
| Submitted ZIP SHA-256 | Not recorded here |

The maintainer confirmed that the already published 0.2.3 package includes hooks.
The current rejection of new uploads does not mean that this existing package
lacks hook support.

The availability statement is based on the maintainer's confirmation. It does not
invent a submission date, approval date, archive identity, or endorsement.

## Version 0.2.4: GitHub Distribution

On 2026-10-26, the maintainer reported that the OpenAI portal blocked the upload
with this message: "Plugins containing hooks cannot be submitted. Remove the
hooks and upload a new ZIP."

All five hooks are essential to the plugin's routing, continuation, safety checks,
artifact validation, and complete responses. They will remain in the package.
Version `0.2.4` will be distributed through GitHub for local installation and will
not be submitted to OpenAI under the current restriction. The GitHub release is
still a draft at the time of this update.

Users who prefer the public marketplace can install `0.2.3`. Users who want the
improvements in `0.2.4` should use its GitHub Windows ZIP when published and follow
the [installation guide](INSTALL_CODEX_PLUGIN.md) for use across existing projects.

OpenAI's [submission documentation](https://developers.openai.com/plugins/deploy/submission)
also describes the restriction on lifecycle hooks. The prepared submission ZIP
and draft listing text are not evidence of an accepted submission.

## How to Update This Record

For a future eligible update, after the portal confirms receipt, record **Submitted — awaiting
review**, record the submission date, and retain the exact submitted version and
SHA-256 from the immutable release asset. Do not present a provisional candidate
hash as final: the authoritative value is calculated from the exact archive that
is published and submitted. Record its source commit separately in the release
evidence. After approval, change the status to **Approved and available**, record the
approval date, and add the official public directory URL.

These status-only edits should use a small documentation pull request. They do
not require a new software version, tag, package, or GitHub Release. Existing
release assets and checksums must remain unchanged.

If OpenAI requests a change to the manifest, hooks, skills, runtime, permissions,
package contents, or user-visible behavior, prepare and validate a new patch
release instead of silently replacing the submitted archive. Pure portal wording
or repository status updates that do not change the package can remain
documentation-only changes.

Keep `0.2.3`'s availability separate from the status of any later update. Do not
remove required hooks merely to make an archive pass the upload checks.

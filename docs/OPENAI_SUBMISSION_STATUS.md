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
| Status | **Release preparation in progress** |
| Plugin version | `0.2.3` |
| Publisher brand | AUTOSOFT Engineering |
| Verified legal publisher | XAVIER MUFFATO LTDA |
| Candidate prepared | Pending the versioned build |
| Submission date | Not yet confirmed |
| Approval date | Not yet applicable |
| Public directory URL | Not yet available |
| OpenAI submission ZIP SHA-256 | Record from the final tagged build before submission |

“Release preparation in progress” means that the repository version is being
prepared for a candidate build; it does not claim that a final candidate exists or
that OpenAI has received, reviewed, approved, endorsed, or published the plugin.

## How to Update This Record

After the portal confirms receipt, change the status to **Submitted — awaiting
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

## Suggested Public Wording

### After Submission

> **OpenAI Plugin Directory status: Submitted — awaiting review.** AI Software
> Architect v0.2.3 was submitted on `YYYY-MM-DD`. Submission does not imply
> approval or endorsement by OpenAI.

### After Approval

> **OpenAI Plugin Directory status: Approved and available.** AI Software
> Architect v0.2.3 was approved on `YYYY-MM-DD` and is available at
> `[official directory URL]`.

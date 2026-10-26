# PR #28 macOS validation evidence

Development validation, not release approval. Observed October 22, 2026
(America/Los_Angeles). These observations precede the candidate commit and PR
branch integration. No tag or public release was published by this validation.

## Candidate identity

| Field | Value |
|---|---|
| Upstream base | `bcc30295440934fc7e56c4acd6fbe14efd53fadf` |
| Local branch | `codex/finish-macos-pr28` (working tree at validation time) |
| Native target | `aarch64-darwin` |
| Candidate version | `0.2.4+codex.pr28.2` |
| macOS host | macOS 27.0.1, arm64 |
| Python / PyInstaller | 3.13.12 / 6.21.0 |
| Codex CLI / app-server | 0.162.1 / 0.163.0 |
| ZIP | `ai-software-architect-v0.2.4+codex.pr28.2-aarch64-darwin.zip` |
| ZIP SHA-256 | `771da04dc75dae27f890998064163856ab0684ac31630fa494091ed05ac1f57e` |
| Plugin provenance SHA-256 | `da1acaa6bca1ec12d3ed446984815fdbaf7023a609832dae444e189921ddb81c` |

The exact archive and a macOS-only checksum file are retained locally under
`dist/pr28-validation/`. This is not the final two-platform publication set.
The older PR checkout and its uncommitted changes were preserved.

## Deterministic checks

| Check | Linux x86-64 | macOS arm64 |
|---|---|---|
| Ruff, including the new release helper | Pass | Pass |
| Strict mypy | Pass | Pass |
| Full pytest | 374 passed, 5 platform skips | 377 passed, 2 Windows skips |
| Native runtime build | Intentionally unsupported | Pass |
| Assembled package validation and hook smoke | Not a Linux package | Pass |
| ZIP extraction, validation, and all-five-hook smoke | Not applicable | Pass |

Windows platform analysis (`mypy --platform win32`) passed on Linux. This is not
native Windows execution. The existing Windows pipeline is retained; its actual
run remains a separate gate after the PR branch is updated.

The lock check passed. Schema and acceptance generators produced no source
changes. The checked-in third-party notice keeps the existing Windows inventory;
macOS notices were generated separately in the isolated native build directory.
Local uv versions differed from CI's pinned 0.11.3; dependency versions came from
the unchanged lockfile. No toolchain or dependency upgrade is included.

## Native package and security checks

- Built the runtime natively on Apple Silicon, then assembled the candidate.
- Extracted its real ZIP using `/usr/bin/ditto` into a path containing spaces and
  an apostrophe, without any permission repair.
- Validated executable permissions, target selection, hook commands, versions,
  and all provenance hashes after extraction.
- Ran the extracted package's hook smoke tester with `PATH=/usr/bin:/bin`.
  The orchestration used developer Python, but each hook invoked the bundled
  executable; no development Python or `uv` was available through that PATH.
- Exercised UserPromptSubmit, PreToolUse, PostToolUse, PostCompact, and Stop.
- Confirmed static snapshot reads, credential-file exclusion, rejection of
  model-written shell commands and appended commands, malicious filename
  handling, invalid artifact rejection, and post-write tamper rejection.
- No project-code marker was created.

The extraction check initially caught a real ZIP metadata defect: permission
bits alone were insufficient for `ditto`. Recording `S_IFREG` with the Unix mode
fixed extraction. The native packaging test now reproduces this round trip.
The smoke workspace is canonicalized before passing its cwd to the hook because
macOS temporary paths may traverse `/var` symlinks; inspection protections were
not relaxed.

## App-server installation and workflow

The package is tested against the existing Mac daemon over SSH and its local
WebSocket control socket. Installation and trust changes use the supported
app-server configuration APIs, without bypassing hook trust.

The final test used the documented structured plugin selection in the prompt,
with the matching app-server mention input, against an isolated copy of the
Expense Insights demo. It inherited the account's `gpt-6.1-sol` default model.
All five installed hooks were enabled and their exact current hashes trusted.

Both the recommendation turn and approval continuation completed. The first
turn compared options and asked for approval without writing artifacts. After
approval, the continuation created exactly the canonical ADR, contract, context,
and implementation-plan files. The live PreToolUse hook validated the proposed
bundle and PostToolUse verified persistence. An independent read of those files
passed the same bundle validator. Every original demo file remained byte-for-byte
unchanged, and the completed trial recorded no shell executions.

The live event stream recorded two UserPromptSubmit completions, three denied
static read requests fulfilled by the hook, one allowed artifact write, one
PostToolUse completion, and two successful Stop completions. PostCompact was
separately exercised by the packaged-runtime smoke test.

Uninstall succeeded. A fresh hooks/list request found no candidate hooks, the
five test-only trust entries were removed, and no runtime process remained.
This verifies the app-server lifecycle, not the Desktop UI lifecycle.
Transport-format probes and idle-timeout runs are excluded from success and
performance evidence. No canonical exploratory-performance ledger was modified.

## Remaining release gates

- Native Windows mypy, tests, build, validation, and hook smoke on Windows.
- Exact two-platform CI artifacts and combined checksum publication set.
- Desktop Plugins-window installation, hook review, and uninstall acceptance.
- A clean-machine installation, including normal downloaded-file quarantine and
  Gatekeeper behavior. The developer Mac and restricted PATH are not substitutes.
- Maintainer review, release approval, and publication.

History-only integration may retain this native evidence only when the tested
runtime, packaging, workflow, and test files are unchanged. Git history identifies
the committed candidate and its integration into the existing PR branch.

Linux native packaging remains outside this contribution.

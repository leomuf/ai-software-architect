<!--
SPDX-FileCopyrightText: 2026 Leonardo Muffato (AUTOSOFT Engineering - www.autosoft-engineering.de)
SPDX-License-Identifier: MIT
-->

# TODO

This file tracks only open work. Completed exploratory evidence remains available in
Git history and the canonical evaluation fixtures.

The canonical release procedure is [`docs/RELEASING.md`](docs/RELEASING.md).
Record the outcome for each candidate from
[`docs/release-evidence-template.md`](docs/release-evidence-template.md); an
unchecked item remains a release blocker unless the recorded release policy defines
an explicit fallback.

## Release blockers

- [ ] Build and install the cleaned control-plane package with a cache-busted version
      supplied during assembly, before provenance hashes are generated.
- [ ] Review and activate the current hooks in Codex Desktop and rerun the five
      exploratory fixtures with `gpt-5.6-sol` at medium reasoning.
- [ ] Confirm that the complete workflow still performs the clarification,
      repository review, and proportionality behaviors through host-native model
      reasoning without language-specific hook routing, returns only user-facing
      Markdown, ends recommendations with visible decision guidance, and accepts
      the immediately following clarification or approval reply without requiring
      another skill invocation.
- [ ] Confirm that the Composite's option-comparison mode renders its stable contract,
      with no internal response markers or HTML comments.
- [ ] Confirm that a single-pattern request loads only its bundled canonical
      reference and makes no MCP or web call.
- [ ] Ensure that a continued architecture comparison uses only bundled canonical
      references and never searches or opens the public GitHub repository merely
      to discover reference content or filenames.
- [ ] Fix and regression-test canonical reference resolution in corrected
      continuation responses; in particular, Dependency Injection must link to
      `dependency-injection.md`, and a response must not escape with a second
      reference defect after the one permitted Stop-hook correction.
- [ ] Confirm that routine dependency reviews submit only bounded
      `dependency_statements`; full source remains limited to an approved
      architecture-boundary check.
- [ ] Measure and reduce exploratory-response latency, especially comparison and
      read-only-review workflows that currently take roughly 90–100 seconds.
      Separate model latency, unnecessary browsing, MCP startup, and Stop-hook
      correction cost before choosing an optimization.
- [ ] Verify native Codex Desktop uninstall on the first attempt immediately after
      a multi-task campaign while Codex remains open, with no manual process
      termination, 15-second retry delay, or plugin-cache editing; capture process
      ownership if the first attempt fails.
- [ ] Run the clean-machine Windows x86-64 acceptance gate without Python, `uv`, or
      a first-run dependency download.
- [ ] If the clean-uninstall gate still fails, omit the persistent MCP integration
      from the release and ship the skills-only Codex package until the host
      lifecycle is proven.

## Forward compatibility

- [ ] Add a compact architecture diagram (preferably Mermaid) to
      `tools/python-mcp/README.md` showing how Codex starts the PowerShell
      launcher, how the packaged MCP runtime is copied into the plugin data
      directory, and how running the private copy prevents the versioned plugin
      cache from being locked during uninstall or update.
- [ ] Add a high-level Mermaid workflow diagram to the Codex section of `README.md`
      and a detailed counterpart to the specification's **Codex control plane**
      section. Show the user prompt, `UserPromptSubmit`, deterministic control
      plane and continuation state, Composite skill, host-model reasoning,
      reference catalog, optional MCP/native tools guarded by `PreToolUse`, `Stop`
      validation and bounded correction, the final response, and approved writes
      limited to `.ai-architect/` artifacts.
- [ ] Test the plugin on at least two more small Python repositories with different
      structures.
- [ ] Add a second-language exploratory pass, beginning with German clarification,
      focused comparison, and approval responses.
- [ ] Validate the public marketplace/release installation flow against an immutable
      release artifact rather than the personal development marketplace.
- [ ] Add operating-system packages only after their clean-machine runtime,
      lifecycle, and security gates pass.

## Deferred until evidence justifies them

- [ ] Consider another deterministic language parser only after its syntax,
      dependency semantics, budgets, and malicious-input fixtures are specified.
- [ ] Consider a focused structural-evidence MCP tool only if repeated reviews still
      require numerous ad hoc host-native probes.
- [ ] Consider a separate lightweight scan skill only if warm control tests show
      skill routing, rather than host/model latency, is the bottleneck.
- [ ] Consider a direct CLI workflow only if users need standalone dependency scans
      outside the architecture-review experience.

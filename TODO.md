<!--
SPDX-FileCopyrightText: 2026 Leonardo Muffato (AUTOSOFT Engineering - www.autosoft-engineering.de)
SPDX-License-Identifier: MIT
-->

# TODO

This file tracks only open work. Completed exploratory evidence remains available in
Git history and the canonical evaluation fixtures.

## Release blockers

- [ ] Build and install the cleaned control-plane package with a cache-busted version
      supplied during assembly, before provenance hashes are generated.
- [ ] Trust the reviewed hooks in Codex Desktop and rerun the five exploratory
      fixtures with `gpt-5.6-sol` at medium reasoning.
- [ ] Confirm that the complete workflow still performs the clarification,
      repository review, and proportionality behaviors through host-native model
      reasoning without language-specific hook routing, emits exactly one
      `clarify`, `recommendation`, or `complete` outcome marker, and requires the
      decision-action marker only for `recommendation`.
- [ ] Confirm that the focused option skill renders its stable comparison contract,
      including the language-neutral decision-action marker.
- [ ] Confirm that a focused single-pattern request injects exactly one bundled
      canonical reference and makes no MCP or web call.
- [ ] Verify native Codex Desktop uninstall on the first attempt immediately after
      a multi-task campaign while Codex remains open, with no manual process
      termination, 120-second retry delay, or plugin-cache editing; capture process
      ownership if the first attempt fails.
- [ ] If the clean-uninstall gate still fails, omit the persistent MCP integration
      from the release and ship the skills-only Codex package until the host
      lifecycle is proven.

## Forward compatibility

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

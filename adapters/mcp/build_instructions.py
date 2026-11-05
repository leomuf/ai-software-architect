# SPDX-FileCopyrightText: 2026 Leonardo Muffato (AUTOSOFT Engineering - www.autosoft-engineering.de)
# SPDX-License-Identifier: MIT

"""Generate one experimental Composite from the shared snapshot; no release build."""

from __future__ import annotations

import argparse
import re
from pathlib import Path, PurePosixPath

from ai_architect_tools.domain.workflow import (
    MCP_MODULE_OVERLAY,
    ReferenceSnapshot,
    canonical_json,
    digest,
)

ROOT = Path(__file__).resolve().parents[2]
PROTOCOL_ID = "orchestrate-architecture-workflow/references/mcp-workflow-protocol.md"


def packaged_path(resource_id: str) -> str:
    path = PurePosixPath(resource_id)
    if path.name == "SKILL.md":
        return f"references/workflow-{path.parent.name}.md"
    return f"references/{path.parts[0]}/{path.name}"


def build(output: Path) -> dict[str, object]:
    snapshot = ReferenceSnapshot(ROOT / "shared/skills")
    output.mkdir(parents=True, exist_ok=True)
    overlay = MCP_MODULE_OVERLAY
    manifest: dict[str, object] = {}
    for resource_id, source in snapshot.contents.items():
        relative = packaged_path(resource_id)
        target = output / relative
        target.parent.mkdir(parents=True, exist_ok=True)

        def rewrite_link(
            match: re.Match[str],
            resource_id: str = resource_id,
            relative: str = relative,
        ) -> str:
            link = match.group(1)
            if "://" in link or link.startswith("#"):
                return match.group(0)
            source_target = (PurePosixPath(resource_id).parent / link).as_posix()
            if source_target not in snapshot.contents:
                return match.group(0)
            # Paths in canonical module bodies are relative to the generated module.
            import posixpath

            return (
                "("
                + posixpath.relpath(
                    packaged_path(source_target),
                    PurePosixPath(relative).parent.as_posix(),
                )
                + ")"
            )

        text = re.sub(r"\(([^\s)]+)\)", rewrite_link, source)
        if resource_id.endswith("/SKILL.md"):
            # Reference modules are plain Markdown, never sibling public skills.
            text = overlay + text.split("---", 2)[2].lstrip()
        target.write_text(text, encoding="utf-8", newline="\n")
        manifest[relative] = {
            "source_id": resource_id,
            "source_sha256": digest(source.encode()),
            "sha256": digest(target.read_bytes()),
        }
    entry = f"""---
name: ai-software-architect-mcp-prototype
description: Use for synthetic architecture guidance and draft bundles in the MCP experiment.
license: MIT
---
<!--
SPDX-FileCopyrightText: 2026 Leonardo Muffato (AUTOSOFT Engineering - www.autosoft-engineering.de)
SPDX-License-Identifier: MIT
-->

# AI Software Architect MCP prototype

Experimental synthetic-only anonymous stateless service; tool contract 0.1.0.
Reference snapshot: `{snapshot.version}`. No account, token or hook is required.

Always load [MCP workflow protocol]({packaged_path(PROTOCOL_ID)}) first.
It overrides canonical modules' host delivery and accepted/persistence wording.
Reason using this host model. No separate model API key is required.

Choose the smallest workflow and load only its modules:

"""
    for resource_id in snapshot.contents:
        if resource_id.endswith("/SKILL.md"):
            entry += f"- [{PurePosixPath(resource_id).parent.name}]({packaged_path(resource_id)})\n"
    entry += """

Focused pattern help loads only the relevant named reference, creates no review
and inspects no repository. Retrieve missing resources by allowlisted ID with
`get_architecture_resource`. Use reference-only mode if transfer is declined.
Keep workflow, comparisons and checkpoints client-local with native host file tools.
Ask before transmitting complete draft artifacts for transient validation/export.
The service stores no review or candidate and cannot resume a lost client checkpoint.
Preserve the user's language and resolve short replies against the local checkpoint.
Discover local checkpoint files after lost context; ask if several reviews match.
Never treat a tool permission dialog or model claim as verified human acceptance.
There is no commit capability. Never claim exported files were installed locally.
"""
    (output / "SKILL.md").write_text(entry, encoding="utf-8", newline="\n")
    result: dict[str, object] = {
        "workflow_version": "0.1.0",
        "tool_contract_version": "0.1.0",
        "reference_version": snapshot.version,
        "files": manifest,
    }
    (output / "provenance.json").write_text(canonical_json(result) + "\n", encoding="utf-8")
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    build(args.output)


if __name__ == "__main__":
    main()

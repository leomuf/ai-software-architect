# SPDX-FileCopyrightText: 2026 Leonardo Muffato (AUTOSOFT Engineering - www.autosoft-engineering.de)
# SPDX-License-Identifier: MIT

"""Read evidence inside the trusted hook; never execute the requested shell tool."""

from __future__ import annotations

import json
import re
from pathlib import Path

try:
    from adapters.codex.repository_snapshot import (
        _is_reparse_point,
        create_repository_snapshot,
        serialize_repository_snapshot,
    )
except ModuleNotFoundError as exc:
    if exc.name != "adapters":
        raise
    from repository_snapshot import (  # type: ignore[import-not-found, no-redef]
        _is_reparse_point,
        create_repository_snapshot,
        serialize_repository_snapshot,
    )

SNAPSHOT_REQUEST = "# ai-software-architect:repository-snapshot"
RESOURCE_REQUEST = "# ai-software-architect:bundled-resource "
EVIDENCE_PREFIX = (
    "The shell operation was denied and was NOT executed. The trusted hook fulfilled "
    "the read request directly. Use the evidence below; do not retry the shell call.\n"
)
MAX_RESOURCE_BYTES = 131_072


def inspection_context() -> str:
    return (
        " Only when repository evidence is needed, request exec_command cmd `"
        + SNAPSHOT_REQUEST
        + "`. For bundled files use cmd `" + RESOURCE_REQUEST
        + "<relative-path>` below the skill root. The trusted hook reads files directly "
        "and returns evidence in the denial reason; shell execution stays denied. "
        "Use returned evidence without retrying. Disclose missing evidence and limits."
    )


def _resource(plugin_root: Path, relative: str) -> str:
    # Only flat packaged Markdown resources; no user-supplied absolute roots.
    if not plugin_root.is_absolute():
        raise ValueError("installed plugin root must be absolute")
    if not re.fullmatch(r"(?:references|assets)/[a-z0-9][a-z0-9-]*\.md", relative):
        raise ValueError("invalid bundled resource path")
    root = plugin_root / "skills" / "ai-software-architect"
    candidate = root / relative
    for path in (
        *plugin_root.parents, plugin_root, plugin_root / "skills",
        root, candidate.parent, candidate,
    ):
        if _is_reparse_point(path):
            raise ValueError("linked bundled resource")
    candidate.resolve(strict=True).relative_to(root.resolve(strict=True))
    if not candidate.is_file():
        raise ValueError("resource is not a regular file")
    with candidate.open("rb") as stream:
        raw = stream.read(MAX_RESOURCE_BYTES + 1)
    if len(raw) > MAX_RESOURCE_BYTES:
        raise ValueError("bundled resource exceeds read budget")
    encoded = json.dumps({"kind": "bundled-resource", "path": relative,
                          "content": raw.decode("utf-8")}, ensure_ascii=True)
    if len(encoded) > MAX_RESOURCE_BYTES:
        raise ValueError("serialized resource exceeds read budget")
    return encoded


def inspection_evidence(
    tool_name: object, tool_input: object, workspace: Path | None, plugin_root: Path | None,
) -> str | None:
    """Return evidence only for exact read requests; the caller must still deny execution."""
    if not isinstance(tool_name, str) or tool_name.rsplit(".", 1)[-1].casefold() not in {
        "bash", "exec_command", "shell_command",
    }:
        return None
    if not isinstance(tool_input, dict):
        return None
    keys = {"cmd", "command"} & tool_input.keys()
    if len(keys) != 1:
        return None
    command = tool_input[next(iter(keys))]
    if not isinstance(command, str):
        return None
    if command != SNAPSHOT_REQUEST and not command.startswith(RESOURCE_REQUEST):
        return None
    try:
        if command == SNAPSHOT_REQUEST:
            if workspace is None or not workspace.is_absolute():
                raise ValueError("host workspace unavailable")
            # Use host cwd only. Never use a root, shell, or workdir from tool_input.
            if any(_is_reparse_point(path) for path in (workspace, *workspace.parents)):
                raise ValueError("linked workspace")
            evidence = serialize_repository_snapshot(
                create_repository_snapshot(workspace)
            ).decode("ascii")
        else:
            if plugin_root is None:
                raise ValueError("installed plugin root unavailable")
            evidence = _resource(plugin_root, command[len(RESOURCE_REQUEST):])
    except (OSError, UnicodeError, ValueError):
        return (
            "The shell operation was denied and was NOT executed. The requested static "
            "evidence could not be read safely. State this limitation; do not use a shell fallback."
        )
    return EVIDENCE_PREFIX + evidence

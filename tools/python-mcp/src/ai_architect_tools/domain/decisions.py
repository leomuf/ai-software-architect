# SPDX-FileCopyrightText: 2026 Leonardo Muffato (AUTOSOFT Engineering - www.autosoft-engineering.de)
# SPDX-License-Identifier: MIT

"""Read and validate ADR frontmatter from the fixed architecture decision directory."""

from __future__ import annotations

import re

from ai_architect_schemas import ArchitectureDecisionArtifact, DecisionListInput, DecisionListResult
from pydantic import ValidationError
from yaml import YAMLError

from .contracts import load_safe_yaml
from .workspace import MAX_FILES, WorkspaceAccessError, WorkspaceReader

_ADR_FILE = re.compile(r"^(ADR-[0-9]{3})(?:-[a-z0-9]+(?:-[a-z0-9]+)*)?\.md$")


def _frontmatter(content: str) -> str:
    lines = content.splitlines()
    if not lines or lines[0] != "---":
        raise ValueError("ADR must begin with YAML frontmatter")
    try:
        end = lines.index("---", 1)
    except ValueError as exc:
        raise ValueError("ADR frontmatter is not closed") from exc
    return "\n".join(lines[1:end])


def list_architecture_decisions(
    reader: WorkspaceReader, request: DecisionListInput
) -> DecisionListResult:
    decisions = []
    invalid_files: list[str] = []
    examined = 0
    skipped = 0
    truncated = False
    try:
        paths = reader.iter_files([".ai-architect/decisions"], {".md"})
        for relative_path in paths:
            if examined >= MAX_FILES:
                truncated = True
                break
            examined += 1
            name = relative_path.rsplit("/", 1)[-1]
            match = _ADR_FILE.fullmatch(name)
            if not match:
                invalid_files.append(relative_path)
                continue
            try:
                content = reader.read_text(relative_path, {".md"})
                artifact = ArchitectureDecisionArtifact.model_validate(
                    load_safe_yaml(_frontmatter(content))
                )
                if artifact.decision.id != match.group(1):
                    raise ValueError("ADR filename id does not match decision id")
                if request.statuses and artifact.decision.status not in request.statuses:
                    continue
                decisions.append(artifact.decision)
            except (WorkspaceAccessError, ValueError, ValidationError, YAMLError):
                invalid_files.append(relative_path)
    except WorkspaceAccessError:
        skipped += 1
    return DecisionListResult(
        decisions=decisions,
        invalid_files=invalid_files,
        files_examined=examined,
        files_skipped=skipped,
        truncated=truncated,
    )


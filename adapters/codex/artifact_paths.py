# SPDX-FileCopyrightText: 2026 Leonardo Muffato (AUTOSOFT Engineering - www.autosoft-engineering.de)
# SPDX-License-Identifier: MIT

"""Canonical repository paths for durable architecture artifacts."""

from __future__ import annotations

import re
from pathlib import Path, PurePosixPath
from typing import Literal

ArtifactKind = Literal["adr", "contract", "context", "implementation-plan"]

_ADR_FILENAME_PATTERN = re.compile(
    r"^ADR-[0-9]{3}(?:-[a-z0-9]+(?:-[a-z0-9]+)*)?\.md$"
)
_FIXED_ARTIFACTS: dict[PurePosixPath, ArtifactKind] = {
    PurePosixPath(".ai-architect/project-context.md"): "context",
    PurePosixPath(".ai-architect/architecture-contract.yaml"): "contract",
    PurePosixPath(".ai-architect/implementation-plan.md"): "implementation-plan",
}


def canonical_artifact_path(
    target: str | Path,
    workspace: Path | None = None,
) -> tuple[Path, ArtifactKind] | None:
    """Return the canonical relative path and kind, or ``None`` when unsupported."""

    raw = str(target).strip()
    if not raw or "\x00" in raw:
        return None
    candidate = Path(raw)
    if candidate.is_absolute():
        if workspace is None:
            return None
        try:
            relative = candidate.resolve(strict=False).relative_to(
                workspace.resolve(strict=False)
            )
        except (OSError, ValueError):
            return None
        normalized = relative.as_posix()
    else:
        normalized = raw.replace("\\", "/")

    segments = normalized.split("/")
    if any(segment in {"", ".", ".."} for segment in segments):
        return None
    canonical = PurePosixPath(*segments)
    fixed_kind = _FIXED_ARTIFACTS.get(canonical)
    if fixed_kind is not None:
        return Path(canonical.as_posix()), fixed_kind
    if (
        canonical.parent == PurePosixPath(".ai-architect/decisions")
        and _ADR_FILENAME_PATTERN.fullmatch(canonical.name) is not None
    ):
        return Path(canonical.as_posix()), "adr"
    return None


def is_canonical_artifact_path(target: str | Path, workspace: Path | None = None) -> bool:
    """Return whether a target is one of the supported durable artifact paths."""

    return canonical_artifact_path(target, workspace) is not None

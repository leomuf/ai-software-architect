# SPDX-FileCopyrightText: 2026 Leonardo Muffato (AUTOSOFT Engineering - www.autosoft-engineering.de)
# SPDX-License-Identifier: MIT

"""Portable complete-bundle rules shared by hooks and the MCP experiment."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from ai_architect_schemas import (
    ArchitectureArtifactBundle,
    ArchitectureContract,
    ArchitectureDecisionArtifact,
    ArtifactSecretScanInput,
)
from ai_architect_schemas.models import DraftArchitectureArtifactBundle

from .artifact_paths import ArtifactKind, canonical_artifact_path
from .contracts import load_safe_yaml, scan_generated_artifact


@dataclass(frozen=True)
class ArtifactCandidate:
    path: Path
    content: str
    kind: ArtifactKind
    operation: str = "Update"


def _yaml_mapping(content: str, *, label: str) -> dict[str, object]:
    raw = load_safe_yaml(content)
    if not isinstance(raw, dict):
        raise ValueError(f"{label} must contain one YAML mapping")
    return raw


def _adr_frontmatter(content: str) -> ArchitectureDecisionArtifact:
    lines = content.splitlines()
    if not lines or lines[0].strip() != "---":
        raise ValueError("ADR must begin with YAML frontmatter")
    try:
        end = next(index for index, line in enumerate(lines[1:], start=1) if line.strip() == "---")
    except StopIteration as exc:
        raise ValueError("ADR YAML frontmatter is not terminated") from exc
    return ArchitectureDecisionArtifact.model_validate(
        _yaml_mapping("\n".join(lines[1:end]), label="ADR frontmatter")
    )


def validate_artifact_bundle_candidates(
    candidates: tuple[ArtifactCandidate, ...],
    *,
    require_complete: bool = False,
    draft: bool = False,
) -> ArchitectureArtifactBundle | DraftArchitectureArtifactBundle | None:
    """Validate a complete multi-file record-and-handoff write atomically."""

    paths: set[Path] = set()
    for candidate in candidates:
        canonical = canonical_artifact_path(candidate.path)
        if canonical is None or canonical != (candidate.path, candidate.kind):
            raise ValueError("unsupported artifact path or kind")
        if candidate.path in paths:
            raise ValueError("duplicate artifact path")
        paths.add(candidate.path)
        if not candidate.content.strip():
            raise ValueError("empty artifact")
        scan = scan_generated_artifact(
            ArtifactSecretScanInput(content=candidate.content, artifact_kind=candidate.kind)
        )
        if not scan.safe_to_write:
            raise ValueError("artifact secret scan failed")
        if candidate.kind == "adr":
            adr = _adr_frontmatter(candidate.content)
            if "-".join(candidate.path.stem.split("-", 2)[:2]) != adr.decision.id:
                raise ValueError("ADR filename and decision id disagree")
    kinds = {candidate.kind for candidate in candidates}
    bundle_kinds = {"adr", "contract", "context", "implementation-plan"}
    if not require_complete and not ("contract" in kinds and len(kinds & bundle_kinds) > 1):
        return None
    missing = sorted(bundle_kinds - kinds)
    if missing:
        raise ValueError(
            "record-and-handoff must write one complete artifact bundle; missing "
            + ", ".join(missing)
        )
    contracts = [candidate for candidate in candidates if candidate.kind == "contract"]
    contexts = [candidate for candidate in candidates if candidate.kind == "context"]
    handoffs = [candidate for candidate in candidates if candidate.kind == "implementation-plan"]
    if len(contracts) != 1 or len(contexts) != 1 or len(handoffs) != 1:
        raise ValueError(
            "record-and-handoff requires exactly one contract, project context, and coding handoff"
        )
    model = DraftArchitectureArtifactBundle if draft else ArchitectureArtifactBundle
    return model.model_validate(
        {
            "contract": ArchitectureContract.model_validate(
                _yaml_mapping(contracts[0].content, label="architecture contract")
            ),
            "decisions": [
                _adr_frontmatter(candidate.content)
                for candidate in candidates
                if candidate.kind == "adr"
            ],
            "project_context": contexts[0].content,
            "coding_handoff": handoffs[0].content,
        }
    )

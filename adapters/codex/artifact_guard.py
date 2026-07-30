# SPDX-FileCopyrightText: 2026 Leonardo Muffato (AUTOSOFT Engineering - www.autosoft-engineering.de)
# SPDX-License-Identifier: MIT

"""Reconstruct and validate proposed architecture artifacts before Codex writes them."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

import yaml
from ai_architect_schemas import (
    ArchitectureArtifactBundle,
    ArchitectureContract,
    ArchitectureDecisionArtifact,
    ArtifactSecretScanInput,
    ContractValidationInput,
)
from ai_architect_tools.domain.contracts import (
    scan_generated_artifact,
    validate_architecture_contract,
)
from pydantic import ValidationError

try:
    from adapters.codex.artifact_paths import ArtifactKind, canonical_artifact_path
except ModuleNotFoundError as exc:
    if exc.name != "adapters":
        raise
    from artifact_paths import (  # type: ignore[import-not-found, no-redef]
        ArtifactKind,
        canonical_artifact_path,
    )

FILE_SECTION_PATTERN = re.compile(
    r"^\*\*\* (Add|Update|Delete) File: (.+)$",
    flags=re.MULTILINE,
)
HUNK_PATTERN = re.compile(r"^@@.*$", flags=re.MULTILINE)


@dataclass(frozen=True)
class ArtifactCandidate:
    path: Path
    content: str
    kind: ArtifactKind
    operation: str = "Update"


def _relative_target(target: str, workspace: Path) -> Path:
    candidate = Path(target.strip())
    if candidate.is_absolute():
        return candidate.resolve(strict=False).relative_to(workspace.resolve(strict=False))
    return candidate


def _added_content(body: str) -> str:
    lines = body.splitlines()
    if any(line and not line.startswith("+") for line in lines):
        raise ValueError("added-file patch contains a non-addition line")
    return "\n".join(line[1:] if line.startswith("+") else "" for line in lines) + "\n"


def _apply_update_patch(original: str, body: str) -> str:
    hunk_matches = tuple(HUNK_PATTERN.finditer(body))
    if not hunk_matches:
        raise ValueError("updated-file patch has no reconstructable hunk")
    current = original.splitlines()
    search_from = 0
    for index, match in enumerate(hunk_matches):
        start = match.end()
        end = hunk_matches[index + 1].start() if index + 1 < len(hunk_matches) else len(body)
        old: list[str] = []
        new: list[str] = []
        for line in body[start:end].lstrip("\r\n").splitlines():
            if line.startswith("\\ No newline at end of file"):
                continue
            if not line or line[0] not in {" ", "+", "-"}:
                raise ValueError("updated-file patch contains an unsupported hunk line")
            if line[0] in {" ", "-"}:
                old.append(line[1:])
            if line[0] in {" ", "+"}:
                new.append(line[1:])
        if not old:
            raise ValueError("updated-file patch has no stable original context")
        locations = [
            position
            for position in range(search_from, len(current) - len(old) + 1)
            if current[position : position + len(old)] == old
        ]
        if len(locations) != 1:
            raise ValueError("updated-file patch context is missing or ambiguous")
        position = locations[0]
        current[position : position + len(old)] = new
        search_from = position + len(new)
    return "\n".join(current) + "\n"


def _patch_candidates(patch: str, workspace: Path) -> tuple[ArtifactCandidate, ...]:
    matches = tuple(FILE_SECTION_PATTERN.finditer(patch))
    if not matches:
        raise ValueError("patch contains no reconstructable file section")
    candidates: list[ArtifactCandidate] = []
    seen: set[Path] = set()
    for index, match in enumerate(matches):
        operation, target = match.groups()
        if operation == "Delete":
            raise ValueError("architecture artifact deletion is not permitted by this workflow")
        relative = _relative_target(target, workspace)
        canonical = canonical_artifact_path(relative)
        if canonical is None:
            raise ValueError(f"unsupported architecture artifact path: {relative.as_posix()}")
        relative, kind = canonical
        if relative in seen:
            raise ValueError(f"patch contains duplicate artifact target: {relative.as_posix()}")
        seen.add(relative)
        start = match.end()
        end = matches[index + 1].start() if index + 1 < len(matches) else patch.find(
            "*** End Patch", start
        )
        if end < 0:
            raise ValueError("patch terminator is missing")
        body = patch[start:end].lstrip("\r\n")
        if operation == "Add":
            content = _added_content(body)
        else:
            source = workspace / relative
            content = _apply_update_patch(source.read_text("utf-8"), body)
        candidates.append(
            ArtifactCandidate(
                path=relative,
                content=content,
                kind=kind,
                operation=operation,
            )
        )
    return tuple(candidates)


def _structured_write_candidate(
    tool_input: object,
    workspace: Path,
) -> tuple[ArtifactCandidate, ...]:
    if not isinstance(tool_input, dict):
        return ()
    target = next(
        (
            tool_input[key]
            for key in ("file_path", "path", "target")
            if isinstance(tool_input.get(key), str)
        ),
        None,
    )
    content = next(
        (
            tool_input[key]
            for key in ("content", "text")
            if isinstance(tool_input.get(key), str)
        ),
        None,
    )
    if target is None:
        return ()
    relative = _relative_target(target, workspace)
    canonical = canonical_artifact_path(relative)
    if canonical is None:
        raise ValueError(f"unsupported architecture artifact path: {relative.as_posix()}")
    relative, kind = canonical
    source = workspace / relative
    old_string = tool_input.get("old_string")
    new_string = tool_input.get("new_string")
    operation = "Update" if source.is_file() else "Add"
    if isinstance(old_string, str) and isinstance(new_string, str):
        original = source.read_text("utf-8")
        if not old_string or original.count(old_string) != 1:
            raise ValueError("structured edit original text is missing or ambiguous")
        content = original.replace(old_string, new_string, 1)
    elif content is None:
        raise ValueError("structured write does not provide complete reconstructable content")
    return (
        ArtifactCandidate(
            path=relative,
            content=content,
            kind=kind,
            operation=operation,
        ),
    )


def proposed_artifact_candidates(
    tool_input: object,
    workspace: Path,
) -> tuple[ArtifactCandidate, ...]:
    try:
        from adapters.codex.control_plane import _patch_text_from_tool_input
    except ModuleNotFoundError as exc:
        if exc.name != "adapters":
            raise
        from control_plane import (  # type: ignore[import-not-found, no-redef]
            _patch_text_from_tool_input,
        )

    patch = _patch_text_from_tool_input(tool_input)
    if patch is not None:
        return _patch_candidates(patch, workspace)
    return _structured_write_candidate(tool_input, workspace)


def _yaml_mapping(content: str, *, label: str) -> dict[str, object]:
    raw = yaml.safe_load(content)
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
) -> ArchitectureArtifactBundle | None:
    """Validate a complete multi-file record-and-handoff write atomically."""

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
    handoffs = [
        candidate for candidate in candidates if candidate.kind == "implementation-plan"
    ]
    if len(contracts) != 1 or len(contexts) != 1 or len(handoffs) != 1:
        raise ValueError(
            "record-and-handoff requires exactly one contract, project context, and coding handoff"
        )
    return ArchitectureArtifactBundle.model_validate(
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


def architecture_artifact_denial_reason(
    tool_input: object,
    workspace: Path,
    *,
    require_complete_bundle: bool = False,
) -> str | None:
    """Return a safe denial reason when a proposed artifact set fails validation."""

    try:
        candidates = proposed_artifact_candidates(tool_input, workspace)
    except (OSError, UnicodeError, ValueError) as exc:
        return (
            "AI Software Architect could not reconstruct the complete proposed "
            f"architecture artifact safely: {exc}. Use one complete reviewable write."
        )
    if not candidates:
        return (
            "AI Software Architect could not identify a complete architecture artifact "
            "candidate, so the write was denied. Use one reviewable canonical write."
        )
    for candidate in candidates:
        if not candidate.content.strip():
            return f"AI Software Architect blocked empty artifact `{candidate.path.as_posix()}`."
        scan = scan_generated_artifact(
            ArtifactSecretScanInput(content=candidate.content, artifact_kind=candidate.kind)
        )
        if not scan.safe_to_write:
            locations = ", ".join(
                f"{finding.category} at line {finding.line}" for finding in scan.findings[:5]
            )
            return (
                f"AI Software Architect blocked `{candidate.path.as_posix()}` because "
                f"the pre-write secret scan reported {locations}."
            )
        if candidate.kind == "contract":
            validation = validate_architecture_contract(
                ContractValidationInput(yaml_content=candidate.content)
            )
            if not validation.valid:
                summary = "; ".join(validation.errors[:5])
                return (
                    f"AI Software Architect blocked `{candidate.path.as_posix()}` because "
                    f"the complete architecture contract is invalid: {summary}. Before "
                    "retrying, reload `assets/artifact-authoring-bundle.md` from the "
                    "installed AI Software Architect skill and preserve the contract "
                    "example's nested object shapes."
                )
        if candidate.kind == "adr":
            try:
                adr = _adr_frontmatter(candidate.content)
            except (ValidationError, ValueError, yaml.YAMLError) as exc:
                return (
                    f"AI Software Architect blocked `{candidate.path.as_posix()}` because "
                    f"its complete ADR frontmatter is invalid: {exc}."
                )
            filename_id = candidate.path.stem.split("-", 2)[:2]
            if "-".join(filename_id) != adr.decision.id:
                return (
                    f"AI Software Architect blocked `{candidate.path.as_posix()}` because "
                    "the ADR filename and decision id disagree."
                )
    try:
        validate_artifact_bundle_candidates(
            candidates,
            require_complete=require_complete_bundle,
        )
    except (ValidationError, ValueError, yaml.YAMLError) as exc:
        return (
            "AI Software Architect blocked the record-and-handoff write because the "
            f"complete artifact bundle is inconsistent: {exc}. Load the exact bundled "
            "ADR, contract, context, and handoff templates, then submit all four artifact "
            "types together in one reviewable write."
        )
    return None

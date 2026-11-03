# SPDX-FileCopyrightText: 2026 Leonardo Muffato (AUTOSOFT Engineering - www.autosoft-engineering.de)
# SPDX-License-Identifier: MIT

"""Filesystem-free candidate validation/export and immutable public references.

There is deliberately no review store, identity, approval, checkpoint or commit.
Only trusted reference files are read during startup, never customer-local paths.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from ai_architect_schemas.mcp_workflow import (
    ARTIFACT_VERSION,
    LocalWorkflowCheckpoint,
    PrepareRequest,
    WorkflowResponse,
)

from .artifact_paths import canonical_artifact_path
from .artifacts import ArtifactCandidate, validate_artifact_bundle_candidates

MAX_EXPORT_BYTES = 128 * 1024
MAX_ARTIFACT_BYTES = 64 * 1024
MCP_MODULE_OVERLAY = (
    "> Anonymous stateless MCP projection. Before using this module, load "
    "orchestrate-architecture-workflow/references/mcp-workflow-protocol.md. "
    "Workflow/checkpoints stay on the client. The protocol's draft-only rules override "
    "canonical accepted/persistence and host-hook instructions. No verified approval or "
    "customer-local writes are provided by the server.\n\n"
)


def canonical_json(value: object) -> str:
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


def digest(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


class WorkflowFailure(Exception):
    def __init__(self, code: str, hint: str) -> None:
        self.code = code
        self.hint = hint
        super().__init__(code)


def success(**data: Any) -> dict[str, Any]:
    return WorkflowResponse(ok=True, data=data).model_dump(mode="json")


class ReferenceSnapshot:
    def __init__(self, root: Path) -> None:
        root = root.resolve(strict=True)
        self.contents: dict[str, str] = {}
        modules = (
            "orchestrate-architecture-workflow",
            "conduct-architecture-interview",
            "evaluate-architecture-options",
            "create-architecture-decisions",
            "prepare-coding-handoff",
            "review-architecture-conformance",
        )
        for module in modules:
            for path in sorted((root / module).rglob("*")):
                if path.suffix not in {".md", ".yaml"} or not path.is_file():
                    continue
                if path.is_symlink() or not path.resolve().is_relative_to(root):
                    raise ValueError("unsafe reference snapshot")
                content = path.read_text("utf-8")
                if len(content.encode()) > MAX_ARTIFACT_BYTES:
                    raise ValueError("oversized reference")
                self.contents[path.relative_to(root).as_posix()] = content
        if not all(f"{module}/SKILL.md" in self.contents for module in modules):
            raise ValueError("incomplete reference snapshot")
        self.contents["protocol/local-workflow-checkpoint.schema.json"] = canonical_json(
            LocalWorkflowCheckpoint.model_json_schema()
        )
        self.version = digest(canonical_json([MCP_MODULE_OVERLAY, self.contents]).encode())

    def get(self, resource_id: str, version: str) -> dict[str, Any]:
        if version not in {"current", self.version}:
            raise WorkflowFailure("version-conflict", "Load the current catalog or pinned service.")
        if resource_id == "catalog":
            return success(reference_version=self.version, resource_ids=sorted(self.contents))
        if resource_id not in self.contents:
            raise WorkflowFailure("not-found", "Choose an allowlisted ID from the catalog.")
        content = self.contents[resource_id]
        if resource_id.endswith("/SKILL.md"):
            content = MCP_MODULE_OVERLAY + content
        return success(
            resource_id=resource_id,
            reference_version=self.version,
            content=content,
            sha256=digest(content.encode()),
        )


def prepare_draft(request: PrepareRequest) -> dict[str, Any]:
    """Validate/export exact submitted bytes without retaining them after the call."""

    if sum(len(file.content.encode()) for file in request.files) > MAX_ARTIFACT_BYTES:
        raise WorkflowFailure("candidate-too-large", "Keep total artifact bytes below 64 KiB.")
    candidates = []
    for file in request.files:
        canonical = canonical_artifact_path(file.path)
        if canonical is None or canonical[0].as_posix() != file.path:
            raise WorkflowFailure("invalid-artifact-path", "Use canonical artifact-relative paths.")
        candidates.append(ArtifactCandidate(canonical[0], file.content, canonical[1]))
    bundle = validate_artifact_bundle_candidates(
        tuple(candidates), require_complete=True, draft=True
    )
    assert bundle is not None
    if bundle.contract.schema_version != ARTIFACT_VERSION or any(
        decision.schema_version != ARTIFACT_VERSION for decision in bundle.decisions
    ):
        raise WorkflowFailure("version-conflict", "Use artifact schema 1.0.0.")
    files = [
        {
            "path": file.path,
            "content": file.content,
            "encoding": "utf-8",
            "size_bytes": len(file.content.encode()),
            "sha256": digest(file.content.encode()),
        }
        for file in sorted(request.files, key=lambda file: file.path)
    ]
    manifest = [{key: value for key, value in file.items() if key != "content"} for file in files]
    return success(
        export={
            "files": files,
            "manifest": manifest,
            "bundle_digest": digest(canonical_json(manifest).encode()),
            "schema_version": ARTIFACT_VERSION,
            "validation": "passed",
            "status": "draft",
            "acceptance": "unverified",
            "local_persistence": "unverified",
        },
        server_retention="none",
        workflow_verification="not-performed",
    )

# SPDX-FileCopyrightText: 2026 Leonardo Muffato (AUTOSOFT Engineering - www.autosoft-engineering.de)
# SPDX-License-Identifier: MIT

"""Static Python import extraction without importing repository code."""

from __future__ import annotations

import ast

from ai_architect_schemas import DependencyEdge, DependencyGraphEvidence, RepositoryAnalysisInput

from .workspace import MAX_FILES, MAX_TOTAL_BYTES, WorkspaceAccessError, WorkspaceReader

MAX_EDGES = 5_000


def _module_name(relative_path: str) -> str:
    module = relative_path.removesuffix(".py").replace("/", ".")
    return module.removesuffix(".__init__")


def analyze_repository_dependencies(
    reader: WorkspaceReader, request: RepositoryAnalysisInput
) -> DependencyGraphEvidence:
    edges: list[DependencyEdge] = []
    warnings: list[str] = []
    examined = 0
    skipped = 0
    total_bytes = 0
    truncated = False

    for relative_path in reader.iter_files(request.relative_roots, {".py"}):
        if examined >= MAX_FILES:
            truncated = True
            break
        try:
            content = reader.read_text(relative_path, {".py"})
            encoded_size = len(content.encode("utf-8"))
            if total_bytes + encoded_size > MAX_TOTAL_BYTES:
                truncated = True
                break
            total_bytes += encoded_size
            tree = ast.parse(content, filename=relative_path)
        except (WorkspaceAccessError, SyntaxError) as exc:
            skipped += 1
            warnings.append(f"Skipped {relative_path}: {type(exc).__name__}")
            continue

        examined += 1
        source = _module_name(relative_path)
        for node in ast.walk(tree):
            targets: list[str] = []
            if isinstance(node, ast.Import):
                targets = [alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom):
                prefix = "." * node.level
                targets = [prefix + (node.module or "")]
            elif isinstance(node, ast.Call) and (
                (isinstance(node.func, ast.Name) and node.func.id == "__import__")
                or (
                    isinstance(node.func, ast.Attribute)
                    and isinstance(node.func.value, ast.Name)
                    and node.func.value.id == "importlib"
                    and node.func.attr == "import_module"
                )
            ):
                warnings.append(
                    f"Dynamic import at {relative_path}:"
                    f"{getattr(node, 'lineno', 1)} was not resolved"
                )
            for target in targets:
                edges.append(
                    DependencyEdge(
                        source=source,
                        target=target,
                        evidence=f"{relative_path}:{getattr(node, 'lineno', 1)}",
                    )
                )
                if len(edges) >= MAX_EDGES:
                    truncated = True
                    break
            if truncated:
                break
        if truncated:
            break

    return DependencyGraphEvidence(
        edges=edges,
        files_examined=examined,
        files_skipped=skipped,
        warnings=warnings[:100],
        truncated=truncated,
    )

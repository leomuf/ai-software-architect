# SPDX-FileCopyrightText: 2026 Leonardo Muffato (AUTOSOFT Engineering - www.autosoft-engineering.de)
# SPDX-License-Identifier: MIT

"""Static Python import extraction without importing repository code."""

from __future__ import annotations

import ast

from ai_architect_schemas import (
    DependencyEdge,
    DependencyGraphEvidence,
    DependencyStatementInput,
    RepositoryAnalysisInput,
)

from .workspace import (
    MAX_FILES,
    MAX_TOTAL_BYTES,
    SourceReader,
    WorkspaceAccessError,
    validate_inline_python_path,
)

MAX_EDGES = 5_000


def _module_name(relative_path: str) -> str:
    module = relative_path.removesuffix(".py").replace("/", ".")
    return module.removesuffix(".__init__")


def _static_targets(node: ast.Import | ast.ImportFrom) -> list[str]:
    if isinstance(node, ast.Import):
        return [alias.name for alias in node.names]
    prefix = "." * node.level
    return [prefix + (node.module or "")]


def _analyze_dependency_statements(
    statements: list[DependencyStatementInput],
) -> DependencyGraphEvidence:
    edges: list[DependencyEdge] = []
    examined_paths: set[str] = set()
    truncated = False
    for item in statements:
        relative_path = validate_inline_python_path(item.relative_path).as_posix()
        try:
            tree = ast.parse(item.statement, filename=relative_path)
        except SyntaxError as exc:
            raise WorkspaceAccessError(
                "invalid-input",
                "dependency statement is not valid Python syntax",
                relative_path,
            ) from exc
        if len(tree.body) != 1 or not isinstance(
            tree.body[0], (ast.Import, ast.ImportFrom)
        ):
            raise WorkspaceAccessError(
                "invalid-input",
                "dependency statement must contain exactly one static import",
                relative_path,
            )
        node = tree.body[0]
        examined_paths.add(relative_path)
        evidence_line = item.start_line + node.lineno - 1
        for target in _static_targets(node):
            edges.append(
                DependencyEdge(
                    source=_module_name(relative_path),
                    target=target,
                    evidence=f"{relative_path}:{evidence_line}",
                )
            )
            if len(edges) >= MAX_EDGES:
                truncated = True
                break
        if truncated:
            break
    return DependencyGraphEvidence(
        edges=edges,
        files_examined=len(examined_paths),
        files_skipped=0,
        warnings=[
            "Fast statement mode analyzes only host-supplied static imports; "
            "dynamic imports and omitted statements are not evaluated"
        ],
        truncated=truncated,
    )


def analyze_repository_dependencies(
    reader: SourceReader | None, request: RepositoryAnalysisInput
) -> DependencyGraphEvidence:
    if request.dependency_statements:
        return _analyze_dependency_statements(request.dependency_statements)
    if reader is None:
        raise WorkspaceAccessError(
            "workspace-unavailable", "dependency evidence source is unavailable"
        )
    edges: list[DependencyEdge] = []
    warnings = (
        ["Inline source mode analyzes only host-supplied files; coverage may be incomplete"]
        if request.source_files
        else []
    )
    examined = 0
    skipped = 0
    total_bytes = 0
    truncated = False

    roots = request.relative_roots or ["."]
    for relative_path in reader.iter_files(roots, {".py"}):
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
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                targets = _static_targets(node)
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

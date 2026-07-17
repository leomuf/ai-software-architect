# SPDX-FileCopyrightText: 2026 Leonardo Muffato (AUTOSOFT Engineering - www.autosoft-engineering.de)
# SPDX-License-Identifier: MIT

"""Command-line diagnostics backed by the same functions as the MCP server."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from ai_architect_schemas import (
    ArtifactSecretScanInput,
    ContractValidationInput,
    DecisionListInput,
    RepositoryAnalysisInput,
)
from pydantic import BaseModel

from .domain.contracts import scan_generated_artifact, validate_architecture_contract
from .domain.decisions import list_architecture_decisions
from .domain.dependencies import analyze_repository_dependencies
from .domain.workspace import WorkspaceReader


def _emit(model: BaseModel) -> None:
    value = model.model_dump(mode="json")
    print(json.dumps(value, indent=2, sort_keys=True))


def _read(path: str) -> str:
    return Path(path).read_text(encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="ai-architect-tools")
    commands = parser.add_subparsers(dest="command", required=True)

    validate = commands.add_parser("validate-contract")
    validate.add_argument("path")

    scan = commands.add_parser("scan-artifact")
    scan.add_argument("path")
    scan.add_argument(
        "--kind", choices=("adr", "contract", "context", "implementation-plan"), required=True
    )

    dependencies = commands.add_parser("analyze-dependencies")
    dependencies.add_argument("--workspace", required=True)
    dependencies.add_argument("roots", nargs="+")

    decisions = commands.add_parser("list-decisions")
    decisions.add_argument("--workspace", required=True)
    decisions.add_argument(
        "--status", action="append", choices=("proposed", "accepted", "rejected", "superseded")
    )
    return parser


def main() -> None:
    args = build_parser().parse_args()
    if args.command == "validate-contract":
        _emit(
            validate_architecture_contract(ContractValidationInput(yaml_content=_read(args.path)))
        )
    elif args.command == "scan-artifact":
        _emit(
            scan_generated_artifact(
                ArtifactSecretScanInput(content=_read(args.path), artifact_kind=args.kind)
            )
        )
    elif args.command == "analyze-dependencies":
        _emit(
            analyze_repository_dependencies(
                WorkspaceReader(Path(args.workspace)),
                RepositoryAnalysisInput(relative_roots=args.roots),
            )
        )
    elif args.command == "list-decisions":
        _emit(
            list_architecture_decisions(
                WorkspaceReader(Path(args.workspace)),
                DecisionListInput(statuses=args.status or []),
            )
        )


if __name__ == "__main__":
    main()

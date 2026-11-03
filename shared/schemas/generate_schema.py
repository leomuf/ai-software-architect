# SPDX-FileCopyrightText: 2026 Leonardo Muffato (AUTOSOFT Engineering - www.autosoft-engineering.de)
# SPDX-License-Identifier: MIT

"""Generate public JSON Schemas from the canonical Pydantic models."""

from __future__ import annotations

import json
from pathlib import Path

from ai_architect_schemas import (
    ArchitectureArtifactBundle,
    ArchitectureContract,
    DraftArchitectureArtifactBundle,
)
from ai_architect_schemas.mcp_workflow import LocalWorkflowCheckpoint, WorkflowWireContracts


def generate_schemas(output_directory: Path) -> None:
    output_directory.mkdir(parents=True, exist_ok=True)
    models = {
        "architecture-contract.schema.json": ArchitectureContract,
        "architecture-artifact-bundle.schema.json": ArchitectureArtifactBundle,
        "draft-architecture-artifact-bundle.schema.json": DraftArchitectureArtifactBundle,
        "mcp-workflow.schema.json": WorkflowWireContracts,
        "local-workflow-checkpoint.schema.json": LocalWorkflowCheckpoint,
    }
    for filename, model in models.items():
        schema = model.model_json_schema()
        schema["$comment"] = (
            "SPDX-FileCopyrightText: 2026 Leonardo Muffato "
            "(AUTOSOFT Engineering - www.autosoft-engineering.de); "
            "SPDX-License-Identifier: MIT"
        )
        (output_directory / filename).write_text(
            json.dumps(schema, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
            newline="\n",
        )


def main() -> None:
    generate_schemas(Path(__file__).parent / "generated")


if __name__ == "__main__":
    main()

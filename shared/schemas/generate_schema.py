# SPDX-FileCopyrightText: 2026 Leonardo Muffato (AUTOSOFT Engineering - www.autosoft-engineering.de)
# SPDX-License-Identifier: MIT

"""Generate public JSON Schemas from the canonical Pydantic models."""

from __future__ import annotations

import json
from pathlib import Path

from ai_architect_schemas import ArchitectureArtifactBundle, ArchitectureContract


def main() -> None:
    generated = Path(__file__).parent / "generated"
    generated.mkdir(parents=True, exist_ok=True)
    models = {
        "architecture-contract.schema.json": ArchitectureContract,
        "architecture-artifact-bundle.schema.json": ArchitectureArtifactBundle,
    }
    for filename, model in models.items():
        schema = model.model_json_schema()
        schema["$comment"] = (
            "SPDX-FileCopyrightText: 2026 Leonardo Muffato "
            "(AUTOSOFT Engineering - www.autosoft-engineering.de); "
            "SPDX-License-Identifier: MIT"
        )
        (generated / filename).write_text(
            json.dumps(schema, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )


if __name__ == "__main__":
    main()

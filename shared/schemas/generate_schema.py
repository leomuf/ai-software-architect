# SPDX-FileCopyrightText: 2026 Leonardo Muffato (AUTOSOFT Engineering - www.autosoft-engineering.de)
# SPDX-License-Identifier: MIT

"""Generate the architecture contract JSON Schema from the canonical Pydantic model."""

from __future__ import annotations

import json
from pathlib import Path

from ai_architect_schemas import ArchitectureContract


def main() -> None:
    output = Path(__file__).parent / "generated" / "architecture-contract.schema.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    schema = ArchitectureContract.model_json_schema()
    schema["$comment"] = (
        "SPDX-FileCopyrightText: 2026 Leonardo Muffato "
        "(AUTOSOFT Engineering - www.autosoft-engineering.de); SPDX-License-Identifier: MIT"
    )
    output.write_text(json.dumps(schema, indent=2, sort_keys=True) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()


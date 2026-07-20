# SPDX-FileCopyrightText: 2026 Leonardo Muffato (AUTOSOFT Engineering - www.autosoft-engineering.de)
# SPDX-License-Identifier: MIT

"""Generate Codex reference metadata from the canonical Markdown references."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REFERENCES = ROOT / "shared" / "skills" / "evaluate-architecture-options" / "references"
OUTPUT = ROOT / "adapters" / "codex" / "reference_catalog.json"
CATEGORIES = {
    "gof": "GoF",
    "architecture": "Architecture",
    "presentation": "Presentation",
    "dependency": "Dependency",
    "data": "Data",
    "integration": "Integration",
    "resilience": "Resilience",
    "modernization": "Modernization",
}
ALIASES = {
    "presentation-model-view-controller.md": ["mvc"],
}


def main() -> None:
    entries: list[dict[str, object]] = []
    for path in sorted(REFERENCES.glob("*.md")):
        if path.name == "no-pattern.md":
            continue
        prefix = path.name.split("-", 1)[0]
        category = CATEGORIES.get(prefix)
        if category is None:
            raise ValueError(f"unknown reference category prefix: {path.name}")
        heading = next(
            line.removeprefix("# ").strip()
            for line in path.read_text("utf-8").splitlines()
            if line.startswith("# ")
        )
        entries.append(
            {
                "name": heading,
                "category": category,
                "filename": path.name,
                "aliases": ALIASES.get(path.name, []),
            }
        )
    OUTPUT.write_text(
        json.dumps({"schema_version": 1, "references": entries}, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )


if __name__ == "__main__":
    main()

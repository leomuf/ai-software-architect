# SPDX-FileCopyrightText: 2026 Leonardo Muffato (AUTOSOFT Engineering - www.autosoft-engineering.de)
# SPDX-License-Identifier: MIT

from __future__ import annotations

from pathlib import Path

from shared.schemas.generate_schema import generate_schemas


def test_generated_json_schemas_use_repository_lf_endings(tmp_path: Path) -> None:
    generate_schemas(tmp_path)
    schemas = sorted(tmp_path.glob("*.json"))

    assert schemas
    for schema in schemas:
        assert b"\r\n" not in schema.read_bytes(), f"{schema.name} contains CRLF endings"

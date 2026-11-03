# SPDX-FileCopyrightText: 2026 Leonardo Muffato (AUTOSOFT Engineering - www.autosoft-engineering.de)
# SPDX-License-Identifier: MIT

from __future__ import annotations

import re
from pathlib import Path

from adapters.mcp.build_instructions import build
from adapters.mcp.prototype_evaluation import schema_risks


def test_one_composite_six_modules_and_resolvable_local_links(tmp_path: Path) -> None:
    manifest = build(tmp_path)
    assert len(list(tmp_path.rglob("SKILL.md"))) == 1
    assert len(list((tmp_path / "references").glob("workflow-*.md"))) == 6
    assert len(list(tmp_path.rglob("gof-*.md"))) == 23
    assert manifest["workflow_version"] == manifest["tool_contract_version"] == "0.1.0"
    assert "draft" in (tmp_path / "SKILL.md").read_text("utf-8")
    for path in tmp_path.rglob("*.md"):
        for target in re.findall(r"\]\(([^\s)]+)\)", path.read_text("utf-8")):
            if "://" not in target and not target.startswith("#"):
                assert (path.parent / target.split("#")[0]).is_file(), (path, target)
    assert not list(tmp_path.rglob("hooks.json"))
    assert not list(tmp_path.rglob(".mcp.json"))  # Endpoint is explicitly configured by operator.


def test_schema_probe_reports_unsupported_shapes_without_removing_constraints() -> None:
    schema = {"nested": {"anyOf": [{"type": "string"}, {"type": "null"}]}}
    assert schema_risks(schema) == ["$.nested.anyOf"]
    assert schema["nested"]["anyOf"][1]["type"] == "null"

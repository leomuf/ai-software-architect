# SPDX-FileCopyrightText: 2026 Leonardo Muffato (AUTOSOFT Engineering - www.autosoft-engineering.de)
# SPDX-License-Identifier: MIT

from __future__ import annotations

import re
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
SPEC = ROOT / "specs" / "AISoftwareArchitect.md"
FEATURE = ROOT / "shared" / "evaluations" / "acceptance.feature"
MANIFEST = ROOT / "shared" / "evaluations" / "verification-manifest.yaml"
NONEXECUTION_FIXTURE = (
    ROOT
    / "shared"
    / "evaluations"
    / "model-fixtures"
    / "repository-code-execution-resistance.yaml"
)
OPTION_COMPARISON_FIXTURE = (
    ROOT
    / "shared"
    / "evaluations"
    / "model-fixtures"
    / "architecture-option-comparison.yaml"
)


def _spec_gherkin() -> str:
    text = SPEC.read_text("utf-8")
    return text.split("```gherkin\n", 1)[1].split("\n```", 1)[0].rstrip() + "\n"


def test_generated_acceptance_is_current_and_every_tag_is_mapped() -> None:
    expected = _spec_gherkin()
    assert FEATURE.read_text("utf-8") == expected
    tags = re.findall(r"^\s*@([A-Z]+-[0-9]{3})$", expected, re.MULTILINE)
    assert len(tags) == len(set(tags)) == 40
    manifest = yaml.safe_load(MANIFEST.read_text("utf-8"))
    assert set(manifest["scenarios"]) == set(tags)
    assert {
        entry["mode"] for entry in manifest["scenarios"].values()
    } == {"deterministic-test", "scripted-host-test", "model-evaluation"}


def test_repository_code_execution_resistance_fixture_is_mapped() -> None:
    fixture = yaml.safe_load(NONEXECUTION_FIXTURE.read_text("utf-8"))
    manifest = yaml.safe_load(MANIFEST.read_text("utf-8"))
    assert fixture["scenario"] == "SEC-011"
    assert "write_text" in fixture["repository"]["hostile.py"]
    assert "import-or-execute-repository-code" in fixture["forbidden_actions"]
    assert manifest["scenarios"]["SEC-011"]["fixture"] == (
        "shared/evaluations/model-fixtures/"
        "repository-code-execution-resistance.yaml"
    )


def test_architecture_option_comparison_fixture_is_mapped() -> None:
    fixture = yaml.safe_load(OPTION_COMPARISON_FIXTURE.read_text("utf-8"))
    manifest = yaml.safe_load(MANIFEST.read_text("utf-8"))
    assert fixture["scenario"] == "FLOW-004"
    assert "list(set(matches))" in fixture["repository"]["budget_book.py"]
    assert "separate-complementary-supporting-patterns" in fixture["expected"]
    assert (
        "import-execute-compile-launch-test-or-build-repository-code"
        in fixture["forbidden_actions"]
    )
    assert manifest["scenarios"]["FLOW-004"]["fixture"] == (
        "shared/evaluations/model-fixtures/architecture-option-comparison.yaml"
    )

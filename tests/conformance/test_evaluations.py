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


def _spec_gherkin() -> str:
    text = SPEC.read_text("utf-8")
    return text.split("```gherkin\n", 1)[1].split("\n```", 1)[0].rstrip() + "\n"


def test_generated_acceptance_is_current_and_every_tag_is_mapped() -> None:
    expected = _spec_gherkin()
    assert FEATURE.read_text("utf-8") == expected
    tags = re.findall(r"^\s*@([A-Z]+-[0-9]{3})$", expected, re.MULTILINE)
    assert len(tags) == len(set(tags)) == 36
    manifest = yaml.safe_load(MANIFEST.read_text("utf-8"))
    assert set(manifest["scenarios"]) == set(tags)
    assert {
        entry["mode"] for entry in manifest["scenarios"].values()
    } == {"deterministic-test", "scripted-host-test", "model-evaluation"}


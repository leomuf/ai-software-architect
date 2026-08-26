# SPDX-FileCopyrightText: 2026 Leonardo Muffato (AUTOSOFT Engineering - www.autosoft-engineering.de)
# SPDX-License-Identifier: MIT

from __future__ import annotations

import json
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
MANIFEST = ROOT / "adapters" / "codex" / "templates" / "plugin.json"
SUBMISSION_ROOT = ROOT / "docs" / "openai-plugin-submission"
PACKAGE_SCRIPT = ROOT / "scripts" / "package-openai-plugin-submission.ps1"


def test_manifest_identifies_company_publisher_and_public_policies() -> None:
    manifest = json.loads(MANIFEST.read_text("utf-8"))

    assert manifest["author"]["name"] == (
        "AUTOSOFT Engineering (a brand of XAVIER MUFFATO LTDA)"
    )
    assert manifest["interface"]["developerName"] == "AUTOSOFT Engineering"
    for field in ("websiteURL", "privacyPolicyURL", "termsOfServiceURL"):
        assert manifest["interface"][field].startswith("https://")


def test_submission_listing_has_three_realistic_starter_prompts() -> None:
    listing = yaml.safe_load((SUBMISSION_ROOT / "listing.yaml").read_text("utf-8"))

    assert listing["publisher"]["display_name"] == "AUTOSOFT Engineering"
    assert (
        listing["publisher"]["developer_identity_to_verify_and_select"]
        == "XAVIER MUFFATO LTDA"
    )
    assert listing["plugin"]["portal_submission_type"] == "Skills only"
    assert len(listing["starter_prompts"]) == 3
    assert all(prompt.strip() for prompt in listing["starter_prompts"])


def test_submission_has_required_positive_and_negative_cases() -> None:
    cases = yaml.safe_load((SUBMISSION_ROOT / "test-cases.yaml").read_text("utf-8"))

    assert len(cases["positive_cases"]) == 5
    assert len(cases["negative_cases"]) == 3
    assert all(case["success_indicators"] for case in cases["positive_cases"])
    assert all(case["success_indicators"] for case in cases["negative_cases"])
    assert all(case["why_not_complete"] for case in cases["negative_cases"])


def test_openai_package_script_preserves_plugin_root() -> None:
    script = PACKAGE_SCRIPT.read_text("utf-8-sig")

    assert "-C $Source ." in script
    assert '".codex-plugin/plugin.json"' in script
    assert '".agents/plugins/marketplace.json"' in script
    assert "validate_plugin.py" in script

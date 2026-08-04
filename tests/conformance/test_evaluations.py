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
AVOID_OVERENGINEERING_FIXTURE = (
    ROOT
    / "shared"
    / "evaluations"
    / "model-fixtures"
    / "avoid-overengineering.yaml"
)
CAMPAIGN_FIXTURES = {
    "clarify-ui-architecture.yaml",
    "architecture-option-comparison.yaml",
    "read-only-architecture-review.yaml",
    "abstract-factory-example.yaml",
    "avoid-overengineering.yaml",
}
COMPLETE_WORKFLOW_EXPECTATIONS = {
    "clarify-ui-architecture.yaml": "end-with-one-visible-focused-question",
    "architecture-option-comparison.yaml": "use-visible-comparison-sections",
    "read-only-architecture-review.yaml": "use-a-visible-single-recommendation-shape",
    "avoid-overengineering.yaml": "use-a-proportionate-visible-recommendation-shape",
}


def _spec_gherkin() -> str:
    text = SPEC.read_text("utf-8")
    return text.split("```gherkin\n", 1)[1].split("\n```", 1)[0].rstrip() + "\n"


def test_generated_acceptance_is_current_and_every_tag_is_mapped() -> None:
    expected = _spec_gherkin()
    assert FEATURE.read_text("utf-8") == expected
    tags = re.findall(r"^\s*@([A-Z]+-[0-9]{3})$", expected, re.MULTILINE)
    assert len(tags) == len(set(tags)) == 49
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
    assert "Inspect the supplied repository" in fixture["prompt"]
    assert "list(set(matches))" in fixture["repository"]["budget_book.py"]
    assert "cite-static-observations-from-budget-book" in fixture["expected"]
    assert (
        "claim-repository-evidence-is-unavailable-while-supplied-source-exists"
        in fixture["forbidden_actions"]
    )
    assert "separate-complementary-supporting-patterns" in fixture["expected"]
    assert (
        "import-execute-compile-launch-test-or-build-repository-code"
        in fixture["forbidden_actions"]
    )
    assert (
        "patch-durable-artifacts-before-required-validation"
        in fixture["continuation"]["forbidden_actions"]
    )
    assert "leave-application-source-unchanged" in fixture["continuation"]["expected"]
    assert manifest["scenarios"]["FLOW-004"]["fixture"] == (
        "shared/evaluations/model-fixtures/architecture-option-comparison.yaml"
    )


def test_exploratory_campaign_covers_all_five_natural_prompts() -> None:
    manifest = yaml.safe_load(MANIFEST.read_text("utf-8"))
    configured = {
        Path(path).name for path in manifest["exploratory_campaign"]
    }
    assert configured == CAMPAIGN_FIXTURES
    for filename in configured:
        fixture = yaml.safe_load(
            (ROOT / "shared" / "evaluations" / "model-fixtures" / filename).read_text(
                "utf-8"
            )
        )
        activation = fixture["activation"]
        assert "plugin_mention" not in activation
        assert activation["skill_invocation"] == "$ai-software-architect"
        assert fixture["prompt"]
        assert fixture["expected"]
        assert fixture["forbidden_actions"]
        visible_shape = COMPLETE_WORKFLOW_EXPECTATIONS.get(filename)
        if visible_shape is not None:
            assert (
                "return-user-facing-markdown-without-internal-control-markers"
                in fixture["expected"]
            )
            assert visible_shape in fixture["expected"]


def test_avoid_overengineering_fixture_requires_evidence_minimization() -> None:
    fixture = yaml.safe_load(AVOID_OVERENGINEERING_FIXTURE.read_text("utf-8"))
    assert fixture["scenario"] == "FLOW-002"
    assert "inspect-the-active-repository" in fixture["forbidden_actions"]
    assert "invoke-any-deterministic-transport" in fixture["forbidden_actions"]
    assert "ask-the-user-to-approve-revise-or-request-more-information" in fixture["expected"]


def test_exploratory_fixtures_match_the_hook_only_codex_architecture() -> None:
    comparison = yaml.safe_load(OPTION_COMPARISON_FIXTURE.read_text("utf-8"))
    assert "start-an-optional-mcp-transport" in comparison["forbidden_actions"]
    assert "load-canonical-artifact-templates-before-drafting" in (
        comparison["continuation"]["expected"]
    )

    review = yaml.safe_load(
        (
            ROOT
            / "shared"
            / "evaluations"
            / "model-fixtures"
            / "read-only-architecture-review.yaml"
        ).read_text("utf-8")
    )
    assert "use-host-native-static-reads" in review["expected"]
    assert "use-one-bounded-static-repository-snapshot-when-exposed" in (
        review["expected"]
    )
    assert (
        "avoid-subagent-delegation-when-the-small-repository-snapshot-is-sufficient"
        in review["expected"]
    )
    assert "list(set(matches))" in review["repository"]["budget_book.py"]
    assert "describe-subagent-results-accurately" in review["expected"]
    assert (
        "claim-independent-reviews-completed-without-successful-subagent-results"
        in review["forbidden_actions"]
    )
    assert "start-an-optional-mcp-transport" in review["forbidden_actions"]

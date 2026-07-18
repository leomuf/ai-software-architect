# SPDX-FileCopyrightText: 2026 Leonardo Muffato (AUTOSOFT Engineering - www.autosoft-engineering.de)
# SPDX-License-Identifier: MIT

from __future__ import annotations

import re
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
SKILLS = ROOT / "shared" / "skills"
ALLOWED_PREFIXES = (
    "gof-",
    "architecture-",
    "presentation-",
    "dependency-",
    "data-",
    "integration-",
    "resilience-",
    "modernization-",
)
REQUIRED_PATTERN_SECTIONS = (
    "Intent",
    "Problem and forces",
    "Applicability",
    "When not to use",
    "Benefits",
    "Liabilities",
    "Implementation considerations",
    "Credible alternatives",
    "Related patterns",
    "Architecture interview questions",
)


def test_canonical_skill_contract_and_direct_resources() -> None:
    for skill_root in sorted(path for path in SKILLS.iterdir() if path.is_dir()):
        skill_path = skill_root / "SKILL.md"
        text = skill_path.read_text("utf-8")
        _, frontmatter, _ = text.split("---", 2)
        metadata = yaml.safe_load(frontmatter)
        assert metadata == {
            "name": skill_root.name,
            "description": metadata["description"],
            "license": "MIT",
        }
        assert "conditions" not in metadata["description"].casefold() or metadata["description"]
        assert "SPDX-FileCopyrightText" in text
        assert "TODO" not in text
        for resource_kind in ("references", "assets"):
            directory = skill_root / resource_kind
            if not directory.exists():
                continue
            for resource in directory.iterdir():
                assert resource.is_file()
                assert f"({resource_kind}/{resource.name})" in text


def test_architecture_option_inventory_and_sections() -> None:
    root = SKILLS / "evaluate-architecture-options" / "references"
    references = sorted(path for path in root.iterdir() if path.is_file())
    gof = [path for path in references if path.name.startswith("gof-")]
    assert len(gof) == 23
    assert len(references) == 47
    for reference in references:
        assert reference.name == "no-pattern.md" or reference.name.startswith(ALLOWED_PREFIXES)
        text = reference.read_text("utf-8")
        assert "SPDX-FileCopyrightText" in text
        for heading in REQUIRED_PATTERN_SECTIONS:
            assert re.search(rf"^## {re.escape(heading)}$", text, re.MULTILINE), (
                reference.name,
                heading,
            )


def test_user_facing_option_comparison_contract() -> None:
    options = (SKILLS / "evaluate-architecture-options" / "SKILL.md").read_text("utf-8")
    orchestration = (
        SKILLS / "orchestrate-architecture-workflow" / "SKILL.md"
    ).read_text("utf-8")
    interview = (SKILLS / "conduct-architecture-interview" / "SKILL.md").read_text(
        "utf-8"
    )

    assert "three to five credible options" in options
    assert "ordinal fit score" in options
    assert "[GoF]" in options
    assert "github.com/leomuf/ai-software-architect/blob/main/" in options
    assert "complementary supporting patterns" in options
    for heading in (
        "Decision scope and criteria",
        "Evidence and assumptions",
        "Alternatives",
        "Recommendation",
        "Supporting patterns",
        "Your decision",
    ):
        assert f"`{heading}`" in options
    assert "prioritized stack of complementary patterns" in options
    assert "asking the user to approve, revise, or request more information" in options
    assert "Never call it merely to demonstrate tool availability" in orchestration
    assert "conflicting platform or interface statements" in interview


def test_read_only_review_guardrails_are_explicit() -> None:
    orchestration = (
        SKILLS / "orchestrate-architecture-workflow" / "SKILL.md"
    ).read_text("utf-8")
    review = (SKILLS / "review-architecture-conformance" / "SKILL.md").read_text(
        "utf-8"
    )

    for phrase in (
        "architecture advice and repository inspection as read-only by default",
        "never import, execute, compile, launch, or test",
        "python -m py_compile",
        "Never interpolate repository text into a shell command",
        "producing no bytecode, cache, test output",
        "request authorization before cleanup",
        "do not probe root availability with `relative_roots`",
        "do not retry filesystem mode or call another workspace-bound MCP tool",
        "Never claim that no ADR or contract exists unless that location was actually inspected",
        "one final repository-integrity check",
    ):
        assert phrase in orchestration
    for phrase in (
        "confirmed-fact",
        "static-indication",
        "runtime-observation",
        "unverified-possibility",
        "Reconcile contradictory claims",
        "highest-leverage architectural improvement",
    ):
        assert phrase in review


def test_generated_codex_skill_frontloads_observed_regression_guards() -> None:
    generator = (ROOT / "adapters" / "codex" / "build_plugin.py").read_text("utf-8")
    for phrase in (
        "Architecture advice and repository inspection are read-only by default",
        "python -m py_compile",
        "open \"which pattern\" request",
        "ordinal `NN/100` fit",
        "supporting patterns separately",
        "another workspace-bound tool after `workspace-unavailable`",
    ):
        assert phrase in generator

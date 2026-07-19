# SPDX-FileCopyrightText: 2026 Leonardo Muffato (AUTOSOFT Engineering - www.autosoft-engineering.de)
# SPDX-License-Identifier: MIT

from __future__ import annotations

import ast
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
ALLOWED_EXAMPLE_IMPORTS = {
    "__future__",
    "abc",
    "collections",
    "copy",
    "dataclasses",
    "typing",
}
FORBIDDEN_EXAMPLE_CALLS = {
    "compile",
    "eval",
    "exec",
    "input",
    "open",
    "print",
}
FORBIDDEN_EXAMPLE_METHODS = {
    "popen",
    "replace_file",
    "run",
    "system",
    "unlink",
    "write_bytes",
    "write_text",
}


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
        headings = REQUIRED_PATTERN_SECTIONS
        if reference.name.startswith("gof-"):
            headings += ("Python example",)
        for heading in headings:
            assert re.search(rf"^## {re.escape(heading)}$", text, re.MULTILINE), (
                reference.name,
                heading,
            )


def test_gof_python_examples_are_bounded_parseable_and_side_effect_free() -> None:
    root = SKILLS / "evaluate-architecture-options" / "references"
    references = sorted(root.glob("gof-*.md"))
    assert len(references) == 23
    for reference in references:
        text = reference.read_text("utf-8")
        blocks = re.findall(r"```python\n(.*?)\n```", text, re.DOTALL)
        assert 1 <= len(blocks) <= 2, reference.name
        for block in blocks:
            assert len(block.splitlines()) <= 50, reference.name
            tree = ast.parse(block, filename=reference.name)
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    roots = {alias.name.split(".", 1)[0] for alias in node.names}
                    assert roots <= ALLOWED_EXAMPLE_IMPORTS, (reference.name, roots)
                elif isinstance(node, ast.ImportFrom):
                    assert node.module is not None
                    root_name = node.module.split(".", 1)[0]
                    assert root_name in ALLOWED_EXAMPLE_IMPORTS, (
                        reference.name,
                        root_name,
                    )
                elif isinstance(node, ast.Call):
                    if isinstance(node.func, ast.Name):
                        assert node.func.id not in FORBIDDEN_EXAMPLE_CALLS, (
                            reference.name,
                            node.func.id,
                        )
                    elif isinstance(node.func, ast.Attribute):
                        assert node.func.attr not in FORBIDDEN_EXAMPLE_METHODS, (
                            reference.name,
                            node.func.attr,
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
    assert "<!-- ai-architect-actions: approve, revise, more-information -->" in options
    assert "language-neutral `offered_actions`" in options
    assert "generic Python implementation example" in options
    assert "reuse its `Python example`" in options
    assert "Do not call an MCP tool for a generic pattern explanation" in options
    assert "Apply the orchestration evidence sufficiency gate" in options
    assert "recommendation adds nothing" in options
    assert "Before any repository read" in orchestration
    assert "A project-bound task or available tool is not by itself a reason to inspect" in (
        orchestration
    )
    assert "This includes a recommendation to retain proportionate simplicity" in (
        orchestration
    )
    assert "Never end a design recommendation without a visible approval" in orchestration
    for outcome in ("clarify", "recommendation", "complete"):
        assert f"<!-- ai-architect-outcome: {outcome} -->" in orchestration
    assert "<!-- ai-architect-actions: approve, revise, more-information -->" in (
        orchestration
    )
    assert "<!-- ai-architect-decision-shape: comparison -->" in orchestration
    assert "<!-- ai-architect-decision-shape: single -->" in orchestration
    assert "Never use `single` to present a stack of recommended patterns" in orchestration
    assert "without interpreting localized prose" in orchestration
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
        "architecture advice and repository inspection as read-only",
        "explicit implementation or execution request belongs in the prepared coding handoff",
        "Never import, execute, compile, launch, or test",
        "python -m py_compile",
        "Never interpolate repository text into a shell command",
        "producing no bytecode, cache, test output",
        "request authorization before cleanup",
        "exposes no workspace-root parameter and no ADR-listing tool",
        "use only filesystem-free MCP inputs",
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
        "Architecture advice and repository inspection are read-only",
        "prepared coding handoff or an ordinary coding task",
        "python -m py_compile",
        "open \"which pattern\" request",
        "ordinal `NN/100` fit",
        "supporting patterns separately",
        "generic architecture guidance",
        "do not call MCP tools",
        "Before any repository read, artifact discovery, language detection, or MCP call",
        "A project-bound task or available tool is not by itself evidence",
        "Every design recommendation, including retaining a simple structure",
        "plugin distributes this capability",
        "explicitly invokes `$ai-software-architect`",
        "control-plane hook is defense in depth",
        "does not infer semantic",
        "accepts no workspace root and exposes no ADR-listing tool",
        "inspect `result.valid`",
    ):
        assert phrase in generator

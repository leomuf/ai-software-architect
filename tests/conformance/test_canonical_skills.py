# SPDX-FileCopyrightText: 2026 Leonardo Muffato (AUTOSOFT Engineering - www.autosoft-engineering.de)
# SPDX-License-Identifier: MIT

from __future__ import annotations

import ast
import re
from pathlib import Path

import yaml
from ai_architect_schemas import ArchitectureContract

from adapters.codex.control_plane import REFERENCE_SPECS
from adapters.codex.reference_catalog import REFERENCE_CATALOG

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
    orchestration = (SKILLS / "orchestrate-architecture-workflow" / "SKILL.md").read_text("utf-8")
    interview = (SKILLS / "conduct-architecture-interview" / "SKILL.md").read_text("utf-8")

    assert "three to five credible options" in options
    assert "ordinal fit score" in options
    assert "not a probability or measured percentage" in options
    assert "exact category and option name" in options
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
    assert "ordinary visible guidance rather than machine-readable comments" in options
    assert "language-neutral `offered_actions`" in options
    assert "generic Python implementation example" in options
    assert "reuse its `Python example`" in options
    assert "need no deterministic tool call" in options
    assert "Apply the orchestration evidence sufficiency gate" in options
    assert "recommendation adds nothing" in options
    assert "Unverified future growth MUST NOT by itself" in options
    assert "Never invent likely growth to justify a pattern" in options
    assert "target 350 to 450 visible words" in options
    assert "soft synthesis budget" in options
    assert "Before any repository read" in orchestration
    assert "A project-bound task or available tool is not by itself a reason to inspect" in (
        orchestration
    )
    assert "Treat a request to improve or choose architecture or design patterns" in (
        orchestration
    )
    assert "Inspect the smallest relevant source set" in options
    assert "Do not claim that repository evidence was unavailable" in options
    assert "retaining proportionate simplicity" in orchestration
    assert "Never end a design recommendation without a visible approval" in orchestration
    assert "Return only user-facing Markdown" in orchestration
    assert "Never emit internal `ai-architect` control" in orchestration
    assert "localized user-decision heading" in orchestration
    assert "Entscheidungsumfang und Kriterien" in options
    assert "Wesentliche Annahme" in options
    assert "Never use a single" in orchestration
    for marker in (
        "ai-architect-outcome:",
        "ai-architect-decision-shape:",
        "ai-architect-actions:",
    ):
        assert marker not in orchestration
    assert "does not infer" in orchestration
    assert "semantic workflow phase from natural-language keywords" in orchestration
    assert "up to three independent read-only reviews" in orchestration
    assert "main agent alone integrates findings" in orchestration
    assert "only when successful subagent results were returned" in orchestration
    assert "never claim that independent reviews completed" in orchestration
    assert "load the exact bundled artifact templates" in orchestration
    assert "conflicting platform or interface statements" in interview


def test_control_plane_reference_registry_matches_canonical_skill_routes() -> None:
    options = (SKILLS / "evaluate-architecture-options" / "SKILL.md").read_text("utf-8")
    routed_files = set(re.findall(r"\(references/([^)]+\.md)\)", options))
    routed_files.discard("no-pattern.md")
    registered_files = {filename for _, filename in REFERENCE_SPECS.values()}
    assert registered_files == routed_files
    assert all(entry.filename in routed_files for entry in REFERENCE_CATALOG.entries)


def test_option_skill_covers_discouraged_pattern_mentions() -> None:
    options = (SKILLS / "evaluate-architecture-options" / "SKILL.md").read_text("utf-8")

    assert "canonical pattern only to discourage or defer it" in options
    assert "Avoid Repository, Unit of Work, and MVC" in options


def test_read_only_review_guardrails_are_explicit() -> None:
    orchestration = (SKILLS / "orchestrate-architecture-workflow" / "SKILL.md").read_text("utf-8")
    review = (SKILLS / "review-architecture-conformance" / "SKILL.md").read_text("utf-8")

    for phrase in (
        "architecture advice and repository inspection as read-only",
        "explicit implementation or execution request belongs in the prepared coding handoff",
        "Never import, execute, compile, launch, or test",
        "test runners, build commands",
        "Never interpolate repository text into a shell command",
        "producing no bytecode, cache, test output",
        "request authorization before cleanup",
        "host-native static analysis",
        "cross-validates the bundle and scans every artifact",
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
        'open "which pattern" request',
        "ordinal `NN/100` fit",
        "not a probability or measured percentage",
        "supporting patterns separately",
        "bare list of catalog pattern names",
        "generic architecture guidance",
        "do not invoke deterministic tools",
        "Before any repository read, artifact discovery, or language detection",
        "A project-bound task or available tool is not by itself evidence",
        "Every design recommendation, including retaining a simple structure",
        "plugin distributes this capability",
        "normal composer",
        "substantive request launched from the plugin",
        "control-plane hooks are defense in depth",
        "does not select a",
        "semantic mode or infer workflow phases",
        "up to three independent read-only",
        "PreToolUse` hook reconstructs proposed",
        "contract example as authoritative for nested list-item shapes",
        "PostToolUse` verifies that the",
    ):
        assert phrase in generator


def test_contract_example_demonstrates_and_validates_nested_shapes() -> None:
    path = (
        SKILLS
        / "create-architecture-decisions"
        / "assets"
        / "architecture-contract.example.yaml"
    )
    contract = ArchitectureContract.model_validate(yaml.safe_load(path.read_text("utf-8")))
    assert contract.quality_attributes
    assert contract.components
    assert contract.external_boundaries
    assert contract.dependency_rules
    assert contract.unresolved_questions

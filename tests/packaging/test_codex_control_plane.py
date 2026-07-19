# SPDX-FileCopyrightText: 2026 Leonardo Muffato (AUTOSOFT Engineering - www.autosoft-engineering.de)
# SPDX-License-Identifier: MIT

from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from pathlib import Path

from adapters.codex import runtime_entry
from adapters.codex.control_plane import (
    DECISION_ACTION_MARKER,
    CodexTurnRoute,
    classify_prompt,
    parse_option_comparison_markdown,
)
from adapters.codex.hook_entry import (
    MAX_STATE_AGE_SECONDS,
    _cleanup_stale_contexts,
    handle_pre_tool_use,
    handle_stop,
    handle_user_prompt_submit,
)

REFERENCE_SLUGS = {
    "gof-abstract-factory",
    "gof-state",
    "gof-strategy",
    "data-repository",
    "presentation-model-view-controller",
}


def _payload(event: str) -> dict[str, object]:
    return {
        "session_id": "session-1",
        "turn_id": "turn-1",
        "hook_event_name": event,
    }


def _plugin_with_reference(tmp_path: Path, slug: str, content: str) -> Path:
    plugin_root = tmp_path / "plugin"
    reference = (
        plugin_root
        / "skills"
        / "evaluate-architecture-options"
        / "references"
        / f"{slug}.md"
    )
    reference.parent.mkdir(parents=True, exist_ok=True)
    reference.write_text(content, encoding="utf-8")
    return plugin_root


def test_activation_uses_host_and_skill_markers_not_natural_language() -> None:
    assert (
        classify_prompt(
            "Documentation says @AI Software Architect, but this is not an invocation.",
            REFERENCE_SLUGS,
        ).route
        == CodexTurnRoute.INACTIVE
    )
    assert (
        classify_prompt(
            "[@AI Software Architect]"
            "(plugin://ai-software-architect@personal) "
            "Suggest a structure.",
            REFERENCE_SLUGS,
        ).route
        == CodexTurnRoute.MISSING_SKILL_INVOCATION
    )
    assert (
        classify_prompt(
            "$ai-software-architect Welche Architektur sollte ich verwenden?",
            REFERENCE_SLUGS,
        ).route
        == CodexTurnRoute.ARCHITECTURE_WORKFLOW
    )
    repository = classify_prompt(
        "$evaluate-architecture-options Zeige ein Beispiel für das Repository pattern.",
        REFERENCE_SLUGS,
    )
    assert repository.route == CodexTurnRoute.PATTERN_REFERENCE
    assert repository.reference_slug == "data-repository"
    assert (
        classify_prompt(
            "$evaluate-architecture-options Compare Strategy and State.",
            REFERENCE_SLUGS,
        ).route
        == CodexTurnRoute.OPTION_COMPARISON
    )
    assert (
        classify_prompt(
            "$evaluate-architecture-options Help me evaluate suitable options.",
            REFERENCE_SLUGS,
        ).route
        == CodexTurnRoute.FOCUSED_WORKFLOW
    )


def test_plugin_uri_without_skill_blocks_before_model_or_mcp(tmp_path: Path) -> None:
    submit = _payload("UserPromptSubmit")
    submit["prompt"] = (
        "[@AI Software Architect](plugin://ai-software-architect@personal) "
        "Please suggest design templates for my project."
    )
    result = handle_user_prompt_submit(submit, tmp_path)
    assert result["decision"] == "block"
    assert "$ai-software-architect" in result["reason"]
    assert "$evaluate-architecture-options" in result["reason"]
    assert not (tmp_path / "control-plane").exists()


def test_focused_reference_is_discovered_from_bundled_files_and_blocks_mcp(
    tmp_path: Path,
) -> None:
    plugin_root = _plugin_with_reference(
        tmp_path,
        "gof-abstract-factory",
        "# Abstract Factory\n\n```python\nfrom typing import Protocol\n```\n",
    )
    submit = _payload("UserPromptSubmit")
    submit["prompt"] = (
        "$evaluate-architecture-options Give an Abstract Factory Python example."
    )
    result = handle_user_prompt_submit(submit, tmp_path / "data", plugin_root)
    additional_context = result["hookSpecificOutput"]["additionalContext"]  # type: ignore[index]
    assert "<bundled-canonical-reference>" in additional_context
    assert "from typing import Protocol" in additional_context
    assert "Do not fetch another copy from the web" in additional_context

    tool = _payload("PreToolUse")
    tool["tool_name"] = "mcp__architect__analyze_python_dependencies"
    blocked = handle_pre_tool_use(tool, tmp_path / "data")
    assert blocked["hookSpecificOutput"]["permissionDecision"] == "deny"  # type: ignore[index]


def test_option_comparison_denies_artifact_tools_but_allows_repository_evidence(
    tmp_path: Path,
) -> None:
    plugin_root = _plugin_with_reference(
        tmp_path,
        "gof-strategy",
        "# Strategy\n",
    )
    _plugin_with_reference(tmp_path, "gof-state", "# State\n")
    submit = _payload("UserPromptSubmit")
    submit["prompt"] = "$evaluate-architecture-options Compare Strategy and State."
    handle_user_prompt_submit(submit, tmp_path / "data", plugin_root)

    validation = _payload("PreToolUse")
    validation["tool_name"] = (
        "mcp__architect__validate_complete_architecture_contract"
    )
    denied = handle_pre_tool_use(validation, tmp_path / "data")
    assert denied["hookSpecificOutput"]["permissionDecision"] == "deny"  # type: ignore[index]

    analysis = _payload("PreToolUse")
    analysis["tool_name"] = "mcp__architect__analyze_python_dependencies"
    assert handle_pre_tool_use(analysis, tmp_path / "data") == {}


def test_option_comparison_rendering_preserves_every_parsed_section(
    tmp_path: Path,
) -> None:
    plugin_root = _plugin_with_reference(tmp_path, "gof-strategy", "# Strategy\n")
    _plugin_with_reference(tmp_path, "gof-state", "# State\n")
    submit = _payload("UserPromptSubmit")
    submit["prompt"] = "$evaluate-architecture-options Compare Strategy and State."
    handle_user_prompt_submit(submit, tmp_path / "data", plugin_root)

    answer = f"""## Decision scope and criteria
Choose the application boundary using change cost and testability.

## Evidence and assumptions
Static evidence is limited; integration volatility is an assumption.

## Alternatives
| Option | Fit | Rationale | Main benefit | Main liability | Material assumption |
| --- | ---: | --- | --- | --- | --- |
| [Architecture] [Hexagonal](https://x/h) | 86/100 | Strong | Isolation | Mapping | Change |
| [Architecture] [Layered](https://x/l) | 72/100 | Familiar | Simple | Erosion | Small team |
| [No pattern] Keep functions | 45/100 | Low ceremony | Cheap | Coupling | Scope stays tiny |

## Recommendation
Choose Hexagonal, with moderate uncertainty.

## Supporting patterns
- [Dependency] [Dependency injection](https://x/di) — supplies adapters.

## Your decision
{DECISION_ACTION_MARKER}
Bitte bestätigen, überarbeiten oder weitere Informationen anfordern.
"""
    parsed = parse_option_comparison_markdown(answer)
    assert parsed.recommended_option_id == "OPT-001"
    assert len(parsed.alternatives) == 3
    assert "integration volatility" in parsed.evidence_and_assumptions
    assert "Dependency injection" in parsed.supporting_patterns
    assert parsed.user_decision_prompt.startswith("Bitte")
    assert parsed.offered_actions == ("approve", "revise", "more-information")

    stop = _payload("Stop")
    stop["stop_hook_active"] = False
    stop["last_assistant_message"] = answer
    assert handle_stop(stop, tmp_path / "data") == {}


def test_stop_requests_one_complete_correction_for_invalid_focused_rendering(
    tmp_path: Path,
) -> None:
    plugin_root = _plugin_with_reference(tmp_path, "gof-strategy", "# Strategy\n")
    _plugin_with_reference(tmp_path, "gof-state", "# State\n")
    submit = _payload("UserPromptSubmit")
    submit["prompt"] = "$evaluate-architecture-options Compare Strategy and State."
    handle_user_prompt_submit(submit, tmp_path / "data", plugin_root)

    stop = _payload("Stop")
    stop["stop_hook_active"] = False
    stop["last_assistant_message"] = "Use Hexagonal Architecture."
    retry = handle_stop(stop, tmp_path / "data")
    assert retry["decision"] == "block"
    assert "complete standalone replacement response" in retry["reason"]
    assert "sections" in retry["reason"]

    stop["stop_hook_active"] = True
    assert handle_stop(stop, tmp_path / "data") == {}


def test_complete_workflow_is_not_semantically_policed_by_keyword_rules(
    tmp_path: Path,
) -> None:
    submit = _payload("UserPromptSubmit")
    submit["prompt"] = (
        "$ai-software-architect Dies ist ein kleines Programm. "
        "Welche Architektur ist angemessen?"
    )
    result = handle_user_prompt_submit(submit, tmp_path)
    assert "complete architecture workflow" in str(result)

    stop = _payload("Stop")
    stop["last_assistant_message"] = (
        "Bleiben Sie zunächst bei einer einfachen Struktur und prüfen Sie diese "
        "Entscheidung erneut, wenn neue Integrationen hinzukommen.\n\n"
        "<!-- ai-architect-outcome: complete -->"
    )
    assert handle_stop(stop, tmp_path) == {}


def test_complete_workflow_requires_exactly_one_supported_outcome_marker(
    tmp_path: Path,
) -> None:
    submit = _payload("UserPromptSubmit")
    submit["prompt"] = "$ai-software-architect Review this architecture."
    handle_user_prompt_submit(submit, tmp_path)

    stop = _payload("Stop")
    stop["last_assistant_message"] = "The review is complete."
    missing = handle_stop(stop, tmp_path)
    assert missing["decision"] == "block"
    assert "exactly one workflow outcome marker" in missing["reason"]

    handle_user_prompt_submit(submit, tmp_path)
    stop["last_assistant_message"] = (
        "The review is complete.\n\n"
        "<!-- ai-architect-outcome: complete -->\n"
        "<!-- ai-architect-outcome: review -->"
    )
    duplicate = handle_stop(stop, tmp_path)
    assert duplicate["decision"] == "block"
    assert "exactly one workflow outcome marker" in duplicate["reason"]

    handle_user_prompt_submit(submit, tmp_path)
    stop["last_assistant_message"] = (
        "The review is complete.\n\n<!-- ai-architect-outcome: review -->"
    )
    unsupported = handle_stop(stop, tmp_path)
    assert unsupported["decision"] == "block"
    assert "clarify, recommendation, or complete" in unsupported["reason"]


def test_complete_workflow_recommendation_requires_decision_action_marker(
    tmp_path: Path,
) -> None:
    submit = _payload("UserPromptSubmit")
    submit["prompt"] = "$ai-software-architect Recommend an architecture."
    handle_user_prompt_submit(submit, tmp_path)

    stop = _payload("Stop")
    stop["last_assistant_message"] = (
        "I recommend a modular monolith.\n\n"
        "<!-- ai-architect-outcome: recommendation -->"
    )
    missing_actions = handle_stop(stop, tmp_path)
    assert missing_actions["decision"] == "block"
    assert "approve, revise, more-information action marker" in missing_actions["reason"]

    handle_user_prompt_submit(submit, tmp_path)
    stop["last_assistant_message"] = (
        "I recommend a modular monolith.\n\n"
        f"{DECISION_ACTION_MARKER}\n"
        "Please approve it, request a revision, or ask for more information.\n\n"
        "<!-- ai-architect-outcome: recommendation -->"
    )
    assert handle_stop(stop, tmp_path) == {}

    handle_user_prompt_submit(submit, tmp_path)
    stop["last_assistant_message"] = (
        "I recommend a modular monolith.\n\n"
        f"{DECISION_ACTION_MARKER}\n"
        "<!-- ai-architect-outcome: recommendation -->"
    )
    missing_guidance = handle_stop(stop, tmp_path)
    assert missing_guidance["decision"] == "block"
    assert "visible localized decision guidance" in missing_guidance["reason"]


def test_complete_workflow_nonrecommendation_rejects_decision_action_marker(
    tmp_path: Path,
) -> None:
    submit = _payload("UserPromptSubmit")
    submit["prompt"] = "$ai-software-architect Clarify the project scope."
    handle_user_prompt_submit(submit, tmp_path)

    stop = _payload("Stop")
    stop["last_assistant_message"] = (
        "Should the interface be a browser UI or a desktop UI?\n\n"
        f"{DECISION_ACTION_MARKER}\n"
        "<!-- ai-architect-outcome: clarify -->"
    )
    invalid = handle_stop(stop, tmp_path)
    assert invalid["decision"] == "block"
    assert "reserved for a recommendation outcome" in invalid["reason"]

    handle_user_prompt_submit(submit, tmp_path)
    stop["last_assistant_message"] = (
        "Should the interface be a browser UI or a desktop UI?\n\n"
        "<!-- ai-architect-outcome: clarify -->"
    )
    assert handle_stop(stop, tmp_path) == {}


def test_turn_state_is_minimal_and_stale_files_are_bounded(tmp_path: Path) -> None:
    submit = _payload("UserPromptSubmit")
    submit["prompt"] = "$ai-software-architect Review this project."
    handle_user_prompt_submit(submit, tmp_path)
    state = next((tmp_path / "control-plane").glob("*.json"))
    state_text = state.read_text("utf-8")
    assert "Review this project" not in state_text
    assert "prompt" not in state_text
    assert set(json.loads(state_text)) == {"active", "reference_slug", "route"}

    old = tmp_path / "control-plane" / "old.json"
    old.write_text("{}\n", encoding="utf-8")
    expired = time.time() - MAX_STATE_AGE_SECONDS - 1
    os.utime(old, (expired, expired))
    _cleanup_stale_contexts(tmp_path)
    assert not old.exists()
    assert state.exists()


def test_runtime_entry_dispatches_hook_mode_as_a_source_script(tmp_path: Path) -> None:
    payload = _payload("UserPromptSubmit")
    payload["prompt"] = "$ai-software-architect Entwirf eine Architektur."
    environment = os.environ.copy()
    environment["PLUGIN_DATA"] = str(tmp_path)
    result = subprocess.run(  # noqa: S603
        [sys.executable, str(Path(runtime_entry.__file__).resolve()), "--codex-hook"],
        input=json.dumps(payload),
        text=True,
        capture_output=True,
        env=environment,
        timeout=10,
        check=True,
    )
    response = json.loads(result.stdout)
    assert "complete architecture workflow" in response["hookSpecificOutput"][
        "additionalContext"
    ]
    assert result.stderr == ""

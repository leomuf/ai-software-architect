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
    CANONICAL_REFERENCE_BASE,
    REQUIRED_COMPARISON_SECTIONS,
    CodexTurnContext,
    CodexTurnRoute,
    classify_prompt,
    developer_context,
    parse_option_comparison_markdown,
    with_reference_hints,
)
from adapters.codex.hook_entry import (
    MAX_CONTINUATION_AGE_SECONDS,
    MAX_STATE_AGE_SECONDS,
    _cleanup_stale_contexts,
    handle_pre_tool_use,
    handle_stop,
    handle_user_prompt_submit,
)


def _payload(event: str) -> dict[str, object]:
    return {
        "session_id": "session-1",
        "turn_id": "turn-1",
        "hook_event_name": event,
    }


def test_activation_uses_host_and_skill_markers_not_natural_language() -> None:
    assert (
        classify_prompt(
            "Documentation says @AI Software Architect, but this is not an invocation.",
        ).route
        == CodexTurnRoute.INACTIVE
    )
    assert (
        classify_prompt(
            "[@AI Software Architect](plugin://ai-software-architect@personal)",
        ).route
        == CodexTurnRoute.MISSING_SKILL_INVOCATION
    )
    assert (
        classify_prompt(
            "[@AI Software Architect]"
            "(plugin://ai-software-architect@personal) "
            "Suggest a structure.",
        ).route
        == CodexTurnRoute.ARCHITECTURE_WORKFLOW
    )
    assert (
        classify_prompt(
            "$ai-software-architect Welche Architektur sollte ich verwenden?",
        ).route
        == CodexTurnRoute.ARCHITECTURE_WORKFLOW
    )
    assert (
        classify_prompt(
            "[$ai-software-architect:ai-software-architect]"
            "(C:\\Users\\Developer\\.codex\\plugins\\cache\\personal\\"
            "ai-software-architect\\version\\skills\\ai-software-architect\\SKILL.md) "
            "Review this project.",
        ).route
        == CodexTurnRoute.ARCHITECTURE_WORKFLOW
    )
    assert (
        classify_prompt(
            "$ai-software-architect Compare Strategy and State.",
        ).route
        == CodexTurnRoute.ARCHITECTURE_WORKFLOW
    )
    assert (
        classify_prompt(
            "$evaluate-architecture-options Compare Strategy and State.",
        ).route
        == CodexTurnRoute.INACTIVE
    )


def test_complete_workflow_context_frontloads_clarification_and_exact_sections() -> None:
    context = developer_context(
        CodexTurnContext(
            active=True,
            route=CodexTurnRoute.ARCHITECTURE_WORKFLOW,
        )
    )
    assert context.index("Apply the clarification gate") < context.index(
        "choose the response structure"
    )
    assert "no repository inspection, no MCP call, and no recommendation" in context
    assert "Option, Fit, Rationale, Main benefit, Main liability, Material assumption" in context
    assert "[No pattern] Keep the script simple" in context
    assert "[GoF] [Strategy]" in context
    assert "installed public skill root `skills/ai-software-architect/`" in context
    assert "Do not resolve them from the plugin root" in context
    positions = [context.index(section) for section in REQUIRED_COMPARISON_SECTIONS]
    assert positions == sorted(positions)


def test_plugin_selection_with_request_enters_architecture_workflow(
    tmp_path: Path,
) -> None:
    submit = _payload("UserPromptSubmit")
    submit["prompt"] = (
        "[@AI Software Architect](plugin://ai-software-architect@personal) "
        "Please suggest design templates for my project."
    )
    result = handle_user_prompt_submit(submit, tmp_path)
    assert "model-selected workflow" in str(result)
    assert (tmp_path / "control-plane").is_dir()


def test_plugin_selection_without_request_blocks_before_model_or_mcp(
    tmp_path: Path,
) -> None:
    submit = _payload("UserPromptSubmit")
    submit["prompt"] = "[@AI Software Architect](plugin://ai-software-architect@personal)"
    result = handle_user_prompt_submit(submit, tmp_path)
    assert result["decision"] == "block"
    assert "without a request" in result["reason"]
    assert "$ai-software-architect" in result["reason"]
    assert not (tmp_path / "control-plane").exists()


def test_single_skill_leaves_pattern_routing_to_the_model(
    tmp_path: Path,
) -> None:
    submit = _payload("UserPromptSubmit")
    submit["prompt"] = "$ai-software-architect Give an Abstract Factory Python example."
    result = handle_user_prompt_submit(submit, tmp_path / "data")
    additional_context = result["hookSpecificOutput"]["additionalContext"]  # type: ignore[index]
    assert "smallest sufficient mode" in additional_context
    assert "references/gof-abstract-factory.md" in additional_context
    assert (
        f"{CANONICAL_REFERENCE_BASE}gof-abstract-factory.md" in additional_context
    )
    assert "do not answer from memory" in additional_context
    assert "do not report the skill unavailable" in additional_context
    assert "complete-candidate-contract" in additional_context
    assert "never patch durable artifacts first" in additional_context.casefold()

    tool = _payload("PreToolUse")
    tool["tool_name"] = "mcp__architect__analyze_python_dependencies"
    assert handle_pre_tool_use(tool, tmp_path / "data") == {}


def test_reference_hints_resolve_explicit_names_without_selecting_a_mode() -> None:
    prompt = "$ai-software-architect Compare the Strategy pattern with State pattern."
    context = with_reference_hints(classify_prompt(prompt), prompt)
    assert context.route == CodexTurnRoute.ARCHITECTURE_WORKFLOW
    assert context.reference_paths == (
        "references/gof-strategy.md",
        "references/gof-state.md",
    )
    ordinary = "$ai-software-architect Review the current state of this project."
    assert with_reference_hints(classify_prompt(ordinary), ordinary).reference_paths == ()
    dependency = "$ai-software-architect Explain Dependency Injection."
    assert with_reference_hints(classify_prompt(dependency), dependency).reference_paths == (
        "references/dependency-injection.md",
    )


def test_single_skill_does_not_infer_mcp_permissions_from_prompt_words(
    tmp_path: Path,
) -> None:
    submit = _payload("UserPromptSubmit")
    submit["prompt"] = "$ai-software-architect Compare Strategy and State."
    handle_user_prompt_submit(submit, tmp_path / "data")

    validation = _payload("PreToolUse")
    validation["tool_name"] = "mcp__architect__validate_complete_architecture_contract"
    assert handle_pre_tool_use(validation, tmp_path / "data") == {}

    analysis = _payload("PreToolUse")
    analysis["tool_name"] = "mcp__architect__analyze_python_dependencies"
    assert handle_pre_tool_use(analysis, tmp_path / "data") == {}


def test_architecture_workflow_blocks_execution_and_allows_static_shell_reads(
    tmp_path: Path,
) -> None:
    submit = _payload("UserPromptSubmit")
    submit["prompt"] = "$ai-software-architect Which design patterns should I use here?"
    handle_user_prompt_submit(submit, tmp_path / "data")

    execution = _payload("PreToolUse")
    execution["tool_name"] = "Bash"
    execution["tool_input"] = {
        "command": "Get-Content budget_book.py; python -m py_compile budget_book.py"
    }
    denied = handle_pre_tool_use(execution, tmp_path / "data")
    assert denied["hookSpecificOutput"]["permissionDecision"] == "deny"  # type: ignore[index]
    assert (
        "does not run interpreters"
        in denied["hookSpecificOutput"][  # type: ignore[index]
            "permissionDecisionReason"
        ]
    )

    assigned_execution = _payload("PreToolUse")
    assigned_execution["tool_name"] = "Bash"
    assigned_execution["tool_input"] = {
        "command": 'foreach ($seed in 1,2) { $result = python -c "print(1)" }'
    }
    assert (
        handle_pre_tool_use(assigned_execution, tmp_path / "data")["hookSpecificOutput"][
            "permissionDecision"
        ]
        == "deny"
    )  # type: ignore[index]

    direct_execution = _payload("PreToolUse")
    direct_execution["tool_name"] = "Bash"
    direct_execution["tool_input"] = {"command": "& .\\scripts\\inspect.py"}
    assert (
        handle_pre_tool_use(direct_execution, tmp_path / "data")["hookSpecificOutput"][
            "permissionDecision"
        ]
        == "deny"
    )  # type: ignore[index]

    static_read = _payload("PreToolUse")
    static_read["tool_name"] = "Bash"
    static_read["tool_input"] = {"command": "Get-Content budget_book.py; git status --short"}
    assert handle_pre_tool_use(static_read, tmp_path / "data") == {}


def test_architect_patch_surface_is_limited_to_architecture_artifacts(
    tmp_path: Path,
) -> None:
    submit = _payload("UserPromptSubmit")
    submit["prompt"] = "$ai-software-architect Record the approved decision."
    handle_user_prompt_submit(submit, tmp_path / "data")

    application_patch = _payload("PreToolUse")
    application_patch["tool_name"] = "apply_patch"
    application_patch["tool_input"] = {
        "patch": "*** Begin Patch\n*** Add File: src/app.py\n+pass\n*** End Patch\n"
    }
    denied = handle_pre_tool_use(application_patch, tmp_path / "data")
    assert denied["hookSpecificOutput"]["permissionDecision"] == "deny"  # type: ignore[index]
    assert (
        ".ai-architect/"
        in denied["hookSpecificOutput"][  # type: ignore[index]
            "permissionDecisionReason"
        ]
    )

    architecture_patch = _payload("PreToolUse")
    architecture_patch["tool_name"] = "apply_patch"
    architecture_patch["tool_input"] = {
        "patch": (
            "*** Begin Patch\n"
            "*** Add File: .ai-architect/decisions/ADR-001.md\n"
            "+# Decision\n"
            "*** End Patch\n"
        )
    }
    assert handle_pre_tool_use(architecture_patch, tmp_path / "data") == {}

    nested_architecture_patch = _payload("PreToolUse")
    nested_architecture_patch["tool_name"] = "apply_patch"
    nested_architecture_patch["tool_input"] = {
        "freeform": {
            "text": (
                "*** Begin Patch\n"
                "*** Add File: .ai-architect/context.md\n"
                "+# Context\n"
                "*** End Patch\n"
            )
        }
    }
    assert handle_pre_tool_use(nested_architecture_patch, tmp_path / "data") == {}

    absolute_staging_patch = _payload("PreToolUse")
    absolute_staging_patch["cwd"] = str(tmp_path)
    absolute_staging_patch["tool_name"] = "apply_patch"
    staging_target = (
        tmp_path
        / ".ai-architect"
        / ".runtime"
        / "staging"
        / "run-1"
        / "ADR-001.md"
    )
    absolute_staging_patch["tool_input"] = {
        "patch": (
            "*** Begin Patch\n"
            f"*** Add File: {staging_target}\n"
            "+# Staged decision\n"
            "*** End Patch\n"
        )
    }
    assert handle_pre_tool_use(absolute_staging_patch, tmp_path / "data") == {}

    escaped_absolute_patch = _payload("PreToolUse")
    escaped_absolute_patch["cwd"] = str(tmp_path)
    escaped_absolute_patch["tool_name"] = "apply_patch"
    escaped_absolute_patch["tool_input"] = {
        "patch": (
            "*** Begin Patch\n"
            f"*** Add File: {tmp_path.parent / 'outside.md'}\n"
            "+unsafe\n"
            "*** End Patch\n"
        )
    }
    escaped = handle_pre_tool_use(escaped_absolute_patch, tmp_path / "data")
    assert escaped["hookSpecificOutput"]["permissionDecision"] == "deny"  # type: ignore[index]


def test_architect_uses_bundled_references_instead_of_web_search(tmp_path: Path) -> None:
    submit = _payload("UserPromptSubmit")
    submit["prompt"] = "$ai-software-architect Compare hexagonal and layered architecture."
    handle_user_prompt_submit(submit, tmp_path / "data")

    web_lookup = _payload("PreToolUse")
    web_lookup["tool_name"] = "WebSearch"
    web_lookup["tool_input"] = {"query": "hexagonal architecture"}
    denied = handle_pre_tool_use(web_lookup, tmp_path / "data")
    assert denied["hookSpecificOutput"]["permissionDecision"] == "deny"  # type: ignore[index]
    assert "bundled" in denied["hookSpecificOutput"]["permissionDecisionReason"]  # type: ignore[index]

    context = handle_user_prompt_submit(submit, tmp_path / "other-data")
    additional = context["hookSpecificOutput"]["additionalContext"]  # type: ignore[index]
    assert (
        "[Architecture] Hexagonal Architecture=references/architecture-hexagonal.md"
        in additional
    )
    assert "assets/architecture-contract.example.yaml" in additional
    assert "Never browse the web" in additional


def test_model_selected_comparison_retains_architecture_artifact_patch_surface(
    tmp_path: Path,
) -> None:
    submit = _payload("UserPromptSubmit")
    submit["prompt"] = "$ai-software-architect Compare Strategy and State."
    handle_user_prompt_submit(submit, tmp_path / "data")

    patch = _payload("PreToolUse")
    patch["tool_name"] = "apply_patch"
    patch["tool_input"] = {
        "patch": (
            "*** Begin Patch\n*** Add File: .ai-architect/notes.md\n+# Notes\n*** End Patch\n"
        )
    }
    assert handle_pre_tool_use(patch, tmp_path / "data") == {}


def test_option_comparison_rendering_preserves_every_parsed_section(
    tmp_path: Path,
) -> None:
    submit = _payload("UserPromptSubmit")
    submit["prompt"] = "$ai-software-architect Compare Strategy and State."
    handle_user_prompt_submit(submit, tmp_path / "data")

    reference_base = (
        "https://github.com/leomuf/ai-software-architect/blob/main/"
        "shared/skills/evaluate-architecture-options/references/"
    )
    hexagonal_row = (
        f"| [Architecture] [Hexagonal]({reference_base}architecture-hexagonal.md) "
        "| **86/100** | Strong | Isolation | Mapping | Change |"
    )
    layered_row = (
        f"| [Architecture] [Layered]({reference_base}architecture-layered.md) "
        "| 72/100 | Familiar | Simple | Erosion | Small team |"
    )
    answer = f"""## Decision scope and criteria
Choose the application boundary using change cost and testability; Fit is an ordinal score.

## Evidence and assumptions
Static evidence is limited; integration volatility is an assumption.

## Alternatives
| Option | Fit | Rationale | Main benefit | Main liability | Material assumption |
| --- | ---: | --- | --- | --- | --- |
{hexagonal_row}
{layered_row}
| [No pattern] Keep functions | 45/100 | Low ceremony | Cheap | Coupling | Scope stays tiny |

## Recommendation
Choose Hexagonal, with moderate uncertainty.

## Supporting patterns
- [Dependency] [Dependency injection]({reference_base}dependency-injection.md) — supplies adapters.

## Your decision
Bitte bestätigen, überarbeiten oder weitere Informationen anfordern.
"""
    parsed = parse_option_comparison_markdown(answer)
    assert parsed.recommended_option_id == "OPT-001"
    assert len(parsed.alternatives) == 3
    assert parsed.alternatives[0].fit_score == 86
    assert "integration volatility" in parsed.evidence_and_assumptions
    assert "Dependency injection" in parsed.supporting_patterns
    assert parsed.user_decision_prompt.startswith("Bitte")

    stop = _payload("Stop")
    stop["stop_hook_active"] = False
    stop["last_assistant_message"] = answer
    assert handle_stop(stop, tmp_path / "data") == {}


def test_comparison_rejects_unlabeled_or_noncanonical_supporting_pattern(
    tmp_path: Path,
) -> None:
    submit = _payload("UserPromptSubmit")
    submit["prompt"] = "$ai-software-architect Which architecture should I use?"
    handle_user_prompt_submit(submit, tmp_path / "data")
    stop = _payload("Stop")
    reference_base = (
        "https://github.com/leomuf/ai-software-architect/blob/main/"
        "shared/skills/evaluate-architecture-options/references/"
    )
    hexagonal_row = (
        f"| [Architecture] [Hexagonal]({reference_base}architecture-hexagonal.md) "
        "| 85/100 | Strong | Isolation | Mapping | Volatility |"
    )
    stop["last_assistant_message"] = f"""## Decision scope and criteria
Choose a boundary using an ordinal fit score.

## Evidence and assumptions
Only stated constraints are confirmed.

## Alternatives
| Option | Fit | Rationale | Main benefit | Main liability | Material assumption |
| --- | ---: | --- | --- | --- | --- |
{hexagonal_row}
| [No pattern] Keep functions | 55/100 | Small | Cheap | Coupling | Stable scope |

## Recommendation
Choose Hexagonal.

## Supporting patterns
- Apply dependency injection through constructors.

## Your decision
Please approve, revise, or request more information.
"""
    result = handle_stop(stop, tmp_path / "data")
    assert result["decision"] == "block"
    assert "canonical public reference" in result["reason"]


def test_stop_requests_one_complete_correction_for_visible_invalid_comparison(
    tmp_path: Path,
) -> None:
    submit = _payload("UserPromptSubmit")
    submit["prompt"] = "$ai-software-architect Compare Strategy and State."
    handle_user_prompt_submit(submit, tmp_path / "data")

    stop = _payload("Stop")
    stop["stop_hook_active"] = False
    stop["last_assistant_message"] = (
        "## Alternatives\nUse Hexagonal Architecture.\n\n"
        "## Your decision\nPlease approve or revise."
    )
    retry = handle_stop(stop, tmp_path / "data")
    assert retry["decision"] == "block"
    assert "complete standalone replacement response" in retry["reason"]
    assert "exact ordered headings" in retry["reason"]
    assert "| Option | Fit | Rationale | Main benefit" in retry["reason"]
    assert "Allowed category labels" in retry["reason"]
    assert "ordinal `NN/100`" in retry["reason"]

    stop["stop_hook_active"] = True
    assert handle_stop(stop, tmp_path / "data") == {}


def test_complete_workflow_is_not_semantically_policed_by_keyword_rules(
    tmp_path: Path,
) -> None:
    submit = _payload("UserPromptSubmit")
    submit["prompt"] = (
        "$ai-software-architect Dies ist ein kleines Programm. Welche Architektur ist angemessen?"
    )
    result = handle_user_prompt_submit(submit, tmp_path)
    assert "model-selected workflow" in str(result)

    stop = _payload("Stop")
    stop["last_assistant_message"] = (
        "Bleiben Sie zunächst bei einer einfachen Struktur und prüfen Sie diese "
        "Entscheidung erneut, wenn neue Integrationen hinzukommen."
    )
    assert handle_stop(stop, tmp_path) == {}


def test_complete_workflow_rejects_internal_response_markers(
    tmp_path: Path,
) -> None:
    submit = _payload("UserPromptSubmit")
    submit["prompt"] = "$ai-software-architect Review this architecture."
    leaked_markers = (
        "<!-- ai-architect-outcome: recommendation -->",
        "<!-- ai-architect-decision-shape: comparison -->",
        "<!-- ai-architect-actions: approve, revise, more-information -->",
        "<!-- internal workflow note -->",
    )
    for marker in leaked_markers:
        handle_user_prompt_submit(submit, tmp_path)
        stop = _payload("Stop")
        stop["last_assistant_message"] = f"Visible answer.\n\n{marker}"
        result = handle_stop(stop, tmp_path)
        assert result["decision"] == "block"
        assert "remove internal control markers or HTML comments" in result["reason"]


def test_complete_workflow_single_recommendation_uses_visible_decision_section(
    tmp_path: Path,
) -> None:
    submit = _payload("UserPromptSubmit")
    submit["prompt"] = "$ai-software-architect Recommend one improvement."
    handle_user_prompt_submit(submit, tmp_path)

    stop = _payload("Stop")
    stop["last_assistant_message"] = """## Recommendation
Extract a pure processing boundary.

## Your decision
Please approve it, request a revision, or ask for more information.
"""
    assert handle_stop(stop, tmp_path) == {}

    handle_user_prompt_submit(submit, tmp_path)
    stop["last_assistant_message"] = """## Recommendation
Extract a pure processing boundary.

## Your decision
"""
    missing_guidance = handle_stop(stop, tmp_path)
    assert missing_guidance["decision"] == "block"
    assert "visible decision guidance" in missing_guidance["reason"]

    handle_user_prompt_submit(submit, tmp_path)
    stop["last_assistant_message"] = """## Recommendation
Extract a pure processing boundary.

## Your decision
## Additional recommendation
Add a second boundary.
"""
    misplaced_content = handle_stop(stop, tmp_path)
    assert misplaced_content["decision"] == "block"
    assert "keep that final section limited" in misplaced_content["reason"]


def test_complete_workflow_comparison_shape_uses_strict_rendering_contract(
    tmp_path: Path,
) -> None:
    submit = _payload("UserPromptSubmit")
    submit["prompt"] = "$ai-software-architect Help me choose an architecture."
    handle_user_prompt_submit(submit, tmp_path)

    stop = _payload("Stop")
    stop["last_assistant_message"] = (
        "## Alternatives\n"
        "Recommended patterns: Strategy, Adapter, and Factory.\n\n"
        "## Your decision\n"
        "Please approve, revise, or request more information."
    )
    invalid = handle_stop(stop, tmp_path)
    assert invalid["decision"] == "block"
    assert "comparison sections" in invalid["reason"]


def test_complete_workflow_clarification_needs_no_machine_marker(
    tmp_path: Path,
) -> None:
    submit = _payload("UserPromptSubmit")
    submit["prompt"] = "$ai-software-architect Clarify the project scope."
    handle_user_prompt_submit(submit, tmp_path)

    stop = _payload("Stop")
    stop["last_assistant_message"] = "Should the interface be a browser UI or a desktop UI?"
    assert handle_stop(stop, tmp_path) == {}


def test_clarification_and_decision_replies_continue_for_one_turn(
    tmp_path: Path,
) -> None:
    first = _payload("UserPromptSubmit")
    first["prompt"] = "$ai-software-architect Which architecture should I use?"
    handle_user_prompt_submit(first, tmp_path)
    stop = _payload("Stop")
    stop["last_assistant_message"] = "Should this be a browser UI or a desktop UI?"
    assert handle_stop(stop, tmp_path) == {}

    follow_up = _payload("UserPromptSubmit")
    follow_up["turn_id"] = "turn-2"
    follow_up["prompt"] = "Desktop UI."
    continued = handle_user_prompt_submit(follow_up, tmp_path)
    assert "bounded continuation" in str(continued)

    complete = _payload("Stop")
    complete["turn_id"] = "turn-2"
    complete["last_assistant_message"] = "The clarification has been recorded."
    assert handle_stop(complete, tmp_path) == {}

    unrelated = _payload("UserPromptSubmit")
    unrelated["turn_id"] = "turn-3"
    unrelated["prompt"] = "What time is it?"
    assert handle_user_prompt_submit(unrelated, tmp_path) == {}


def test_decision_approval_continuation_requires_record_and_handoff(
    tmp_path: Path,
) -> None:
    first = _payload("UserPromptSubmit")
    first["prompt"] = "$ai-software-architect Which architecture should I use?"
    handle_user_prompt_submit(first, tmp_path)
    stop = _payload("Stop")
    stop["last_assistant_message"] = (
        "## Recommendation\nChoose Strategy.\n\n"
        "## Your decision\nPlease approve, revise, or request more information."
    )
    assert handle_stop(stop, tmp_path) == {}

    approval = _payload("UserPromptSubmit")
    approval["turn_id"] = "turn-2"
    approval["prompt"] = "Approve this recommendation."
    continued = handle_user_prompt_submit(approval, tmp_path)
    additional = continued["hookSpecificOutput"]["additionalContext"]  # type: ignore[index]
    assert "record_and_handoff" in additional
    assert "do not merely acknowledge approval" in additional
    assert "Approval never authorizes application-code changes" in additional
    assert "original request explicitly prohibited" in additional


def test_clarification_continuation_resumes_design_without_recording(
    tmp_path: Path,
) -> None:
    first = _payload("UserPromptSubmit")
    first["prompt"] = "$ai-software-architect Clarify this."
    handle_user_prompt_submit(first, tmp_path)
    stop = _payload("Stop")
    stop["last_assistant_message"] = "Should this be a desktop or web application?"
    assert handle_stop(stop, tmp_path) == {}

    answer = _payload("UserPromptSubmit")
    answer["turn_id"] = "turn-2"
    answer["prompt"] = "Desktop."
    continued = handle_user_prompt_submit(answer, tmp_path)
    additional = continued["hookSpecificOutput"]["additionalContext"]  # type: ignore[index]
    assert "requested clarification" in additional
    assert "resume the smallest sufficient architecture workflow" in additional
    assert "transition to `record_and_handoff`" not in additional


def test_another_explicit_skill_cancels_pending_architect_continuation(
    tmp_path: Path,
) -> None:
    first = _payload("UserPromptSubmit")
    first["prompt"] = "$ai-software-architect Recommend one option."
    handle_user_prompt_submit(first, tmp_path)
    stop = _payload("Stop")
    stop["last_assistant_message"] = (
        "## Your decision\nPlease approve, revise, or request more information."
    )
    assert handle_stop(stop, tmp_path) == {}

    other = _payload("UserPromptSubmit")
    other["turn_id"] = "turn-2"
    other["prompt"] = "$another-skill Do something unrelated."
    assert handle_user_prompt_submit(other, tmp_path) == {}


def test_pending_architect_continuation_expires(tmp_path: Path) -> None:
    first = _payload("UserPromptSubmit")
    first["prompt"] = "$ai-software-architect Clarify this decision."
    handle_user_prompt_submit(first, tmp_path)
    stop = _payload("Stop")
    stop["last_assistant_message"] = "Which deployment target should be used?"
    assert handle_stop(stop, tmp_path) == {}
    continuation = next((tmp_path / "control-plane").glob("continuation-*.json"))
    expired = time.time() - MAX_CONTINUATION_AGE_SECONDS - 1
    os.utime(continuation, (expired, expired))

    reply = _payload("UserPromptSubmit")
    reply["turn_id"] = "turn-2"
    reply["prompt"] = "Local desktop."
    assert handle_user_prompt_submit(reply, tmp_path) == {}
    assert not continuation.exists()


def test_turn_state_is_minimal_and_stale_files_are_bounded(tmp_path: Path) -> None:
    submit = _payload("UserPromptSubmit")
    submit["prompt"] = "$ai-software-architect Review this project."
    handle_user_prompt_submit(submit, tmp_path)
    state = next((tmp_path / "control-plane").glob("*.json"))
    state_text = state.read_text("utf-8")
    assert "Review this project" not in state_text
    assert "prompt" not in state_text
    assert set(json.loads(state_text)) == {"active", "reference_paths", "route"}

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
    assert "model-selected workflow" in response["hookSpecificOutput"]["additionalContext"]
    assert result.stderr == ""

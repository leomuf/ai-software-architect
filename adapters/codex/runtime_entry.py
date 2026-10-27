# SPDX-FileCopyrightText: 2026 Leonardo Muffato (AUTOSOFT Engineering - www.autosoft-engineering.de)
# SPDX-License-Identifier: MIT

"""PyInstaller entry point for the short-lived Codex control-plane runtime."""

from __future__ import annotations

import json
import sys
from collections.abc import Callable


def _hook_entrypoint() -> Callable[[str | None], None]:
    """Load hook dependencies for both startup checks and normal hook dispatch."""
    try:
        from adapters.codex.hook_entry import main as hook_main
    except ModuleNotFoundError as exc:
        if exc.name != "adapters":
            raise
        from hook_entry import main as hook_main  # type: ignore[import-not-found, no-redef]

    return hook_main


def main() -> None:
    arguments = sys.argv[1:]
    if arguments == ["--self-test"]:
        # Import the hook dependencies without handling input or touching project/state files.
        if not callable(_hook_entrypoint()):
            raise RuntimeError("hook entry point is unavailable")
        print(json.dumps({"status": "ok", "runtime": "ai-architect-runtime"}))
        return
    if arguments == ["--repository-snapshot", "--root", "."]:
        try:
            from adapters.codex.repository_snapshot import main as snapshot_main
        except ModuleNotFoundError as exc:
            if exc.name != "adapters":
                raise
            from repository_snapshot import (  # type: ignore[import-not-found, no-redef]
                main as snapshot_main,
            )

        snapshot_main()
        return

    if (
        len(arguments) == 3
        and arguments[:2] == ["--codex-hook", "--event"]
        and arguments[2]
        in {"UserPromptSubmit", "PreToolUse", "PostToolUse", "PostCompact", "Stop"}
    ):
        _hook_entrypoint()(arguments[2])
        return

    raise SystemExit(
        "use --self-test, --codex-hook --event <event>, or --repository-snapshot --root .; "
        "this runtime does not start a persistent server"
    )

if __name__ == "__main__":
    main()

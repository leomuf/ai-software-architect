# SPDX-FileCopyrightText: 2026 Leonardo Muffato (AUTOSOFT Engineering - www.autosoft-engineering.de)
# SPDX-License-Identifier: MIT

"""PyInstaller entry point for the short-lived Codex control-plane runtime."""

from __future__ import annotations

import sys


def main() -> None:
    arguments = sys.argv[1:]
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
        try:
            from adapters.codex.hook_entry import main as hook_main
        except ModuleNotFoundError as exc:
            if exc.name != "adapters":
                raise
            from hook_entry import main as hook_main  # type: ignore[import-not-found, no-redef]

        hook_main(expected_event=arguments[2])
        return

    raise SystemExit(
        "use --codex-hook --event <event> or --repository-snapshot --root .; "
        "this runtime does not start a persistent server"
    )

if __name__ == "__main__":
    main()

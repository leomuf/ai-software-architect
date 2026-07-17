# SPDX-FileCopyrightText: 2026 Leonardo Muffato (AUTOSOFT Engineering - www.autosoft-engineering.de)
# SPDX-License-Identifier: MIT

"""Launch the packaged STDIO runtime and exercise pathless contract validation."""

from __future__ import annotations

import argparse
import asyncio
import tempfile
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

EXPECTED_TOOLS = {
    "validate_architecture_contract",
    "list_architecture_decisions",
    "analyze_repository_dependencies",
    "check_architecture_boundaries",
    "scan_generated_artifact",
}


async def smoke_test(executable: Path) -> None:
    parameters = StdioServerParameters(command=str(executable.resolve()), args=[])
    with tempfile.TemporaryFile(mode="w+", encoding="utf-8") as errlog:
        async with stdio_client(parameters, errlog=errlog) as (read_stream, write_stream):
            async with ClientSession(read_stream, write_stream) as session:
                initialized = await session.initialize()
                tools = await session.list_tools()
                names = {tool.name for tool in tools.tools}
                if names != EXPECTED_TOOLS:
                    raise RuntimeError(f"unexpected tool set: {sorted(names)}")
                result = await session.call_tool(
                    "validate_architecture_contract",
                    arguments={
                        "request": {
                            "yaml_content": (
                                "schema_version: 1.0.0\nrevision: 1\nscope: smoke-test\n"
                            )
                        }
                    },
                )
                if result.isError:
                    raise RuntimeError(f"pathless validation failed: {result.content}")
                print(
                    f"{initialized.serverInfo.name}: {len(names)} tools; validation succeeded"
                )
        errlog.seek(0)
        stderr = errlog.read()
        if "Traceback" in stderr:
            raise RuntimeError(f"runtime wrote a traceback to stderr:\n{stderr}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("executable", type=Path)
    args = parser.parse_args()
    asyncio.run(smoke_test(args.executable))


if __name__ == "__main__":
    main()

# SPDX-FileCopyrightText: 2026 Leonardo Muffato (AUTOSOFT Engineering - www.autosoft-engineering.de)
# SPDX-License-Identifier: MIT

"""Anonymous, stateless HTTP prototype. Project workflow state stays on the client."""

from __future__ import annotations

import argparse
import json
import logging
import time
from collections import deque
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

import mcp.types as types
import uvicorn
import yaml
from ai_architect_schemas import StrictModel
from ai_architect_schemas.mcp_workflow import (
    CONTRACT_VERSION,
    EmptyRequest,
    PrepareRequest,
    ResourceRequest,
    WorkflowError,
    WorkflowResponse,
)
from mcp.server.lowlevel import Server
from mcp.server.streamable_http_manager import StreamableHTTPSessionManager
from pydantic import ValidationError
from starlette.applications import Starlette
from starlette.responses import JSONResponse
from starlette.routing import Route
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from .domain.workflow import (
    MAX_ARTIFACT_BYTES,
    MAX_EXPORT_BYTES,
    ReferenceSnapshot,
    WorkflowFailure,
    canonical_json,
    prepare_draft,
    success,
)

PROTOCOL_VERSION = "2025-11-25"
MAX_REQUEST_BYTES = 256 * 1024
TOOL_CONTRACTS: dict[str, tuple[type[StrictModel], str]] = {
    "get_architecture_capabilities": (
        EmptyRequest,
        "Discover anonymous stateless capabilities and privacy limits; no project data.",
    ),
    "get_architecture_resource": (
        ResourceRequest,
        "Retrieve one allowlisted reference or catalog; no project context required.",
    ),
    "prepare_architecture_bundle": (
        PrepareRequest,
        "Validate and export complete proposed draft bytes in one call. "
        "Contents are transmitted for processing, never stored. "
        "No verified approval or local writes.",
    ),
}


def failure(code: str, hint: str, *, retryable: bool = False) -> dict[str, Any]:
    return WorkflowResponse(
        ok=False,
        error=WorkflowError(
            code=code,
            repair_hint=hint,
            retryable=retryable,
        ),
    ).model_dump(mode="json")


def tool_result(payload: dict[str, Any]) -> types.CallToolResult:
    result = types.CallToolResult(
        isError=not payload["ok"],
        structuredContent=payload,
        content=[types.TextContent(type="text", text=canonical_json(payload))],
    )
    if len(result.model_dump_json().encode()) + 256 > MAX_EXPORT_BYTES:
        return tool_result(failure("result-too-large", "Reduce artifact or reference size."))
    return result


def create_server(references: ReferenceSnapshot) -> Server[Any, Any]:
    server: Server[Any, Any] = Server(
        "ai-software-architect-phase-0",
        version=CONTRACT_VERSION,
        instructions="Anonymous stateless architecture reference/validation service. "
        "Load the Composite and MCP protocol. "
        "Keep workflow, checkpoints and reasoning client-local. "
        "Ask before transmitting project artifacts; reference-only use sends no project context. "
        "Draft export only; no verified approval, server reviews or customer-local writes.",
    )

    @server.list_tools()  # type: ignore[no-untyped-call, untyped-decorator]
    async def list_tools() -> list[types.Tool]:
        return [
            types.Tool(
                name=name,
                description=description,
                inputSchema=model.model_json_schema(),
                outputSchema=WorkflowResponse.model_json_schema(),
                annotations=types.ToolAnnotations(
                    readOnlyHint=True,
                    destructiveHint=False,
                    idempotentHint=True,
                    openWorldHint=False,
                ),
            )
            for name, (model, description) in TOOL_CONTRACTS.items()
        ]

    # SDK diagnostics may include request values; validate only inside this sanitized boundary.
    @server.call_tool(validate_input=False)  # type: ignore[untyped-decorator]
    async def call_tool(name: str, arguments: dict[str, Any]) -> types.CallToolResult:
        try:
            contract = TOOL_CONTRACTS.get(name)
            if contract is None:
                raise WorkflowFailure(
                    "unsupported-operation", "Use the advertised stateless tools."
                )
            request = contract[0].model_validate(arguments)
            if isinstance(request, ResourceRequest):
                payload = references.get(request.resource_id, request.reference_version)
            elif isinstance(request, PrepareRequest):
                payload = prepare_draft(request)
            else:
                payload = success(
                    contract_version=CONTRACT_VERSION,
                    protocol=PROTOCOL_VERSION,
                    reference_version=references.version,
                    authentication="none",
                    server_retention="none",
                    workflow_state="client-local",
                    acceptance="unverified",
                    local_persistence="unverified",
                    capabilities=["references", "complete-draft-validation", "inline-draft-export"],
                    max_request_bytes=MAX_REQUEST_BYTES,
                    max_artifact_bytes=MAX_ARTIFACT_BYTES,
                    max_response_bytes=MAX_EXPORT_BYTES,
                    disclosure="Bundle bytes leave the client for transient validation. "
                    "Use reference-only or explicitly selected local deployment if declined.",
                )
        except WorkflowFailure as exc:
            payload = failure(exc.code, exc.hint)
        except (ValidationError, ValueError, yaml.YAMLError, RecursionError):
            payload = failure(
                "invalid-input", "Check the schema and complete proposed-bundle invariants."
            )
        except Exception:
            payload = failure(
                "internal-error", "Retry the same self-contained request.", retryable=True
            )
        return tool_result(payload)

    return server


def check_json_depth(body: bytes | bytearray) -> None:
    depth = 0
    quoted = escaped = False
    for char in body:
        if quoted:
            if escaped:
                escaped = False
            elif char == 92:
                escaped = True
            elif char == 34:
                quoted = False
        elif char == 34:
            quoted = True
        elif char in (123, 91):
            depth += 1
            if depth > 32:
                raise ValueError("JSON nesting limit exceeded")
        elif char in (125, 93):
            depth -= 1


def unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result = dict(pairs)
    if len(result) != len(pairs):
        raise ValueError("duplicate JSON key")
    return result


class ExperimentBoundary:
    def __init__(self, app: ASGIApp, public_url: str, *, loopback_http: bool) -> None:
        self.app = app
        self.url = urlsplit(public_url)
        if (
            self.url.scheme not in {"http", "https"}
            or self.url.username
            or self.url.password
            or self.url.path != "/mcp"
            or self.url.query
            or self.url.fragment
            or not self.url.hostname
        ):
            raise ValueError("public_url must be an absolute /mcp URL")
        if self.url.scheme != "https" and not (
            loopback_http and self.url.hostname in {"127.0.0.1", "localhost", "::1"}
        ):
            raise ValueError("HTTPS required outside explicit loopback tests")
        # Short-lived infrastructure counters only; no project payloads, accounts or tokens.
        self.calls: dict[str, deque[float]] = {}

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        async def no_store_send(message: Message) -> None:
            if message["type"] == "http.response.start":
                message = {
                    **message,
                    "headers": [
                        *message.get("headers", []),
                        (b"cache-control", b"no-store"),
                        (b"pragma", b"no-cache"),
                    ],
                }
            await send(message)

        async def reject(code: str, status: int) -> None:
            await JSONResponse({"error": code}, status_code=status)(scope, receive, no_store_send)

        headers = {key.lower(): value for key, value in scope["headers"]}
        if headers.get(b"host", b"").decode("latin1") != self.url.netloc or headers.get(
            b"origin", b""
        ).decode("latin1") not in {"", f"{self.url.scheme}://{self.url.netloc}"}:
            await reject("invalid-origin-or-host", 403)
            return
        if scope.get("scheme") != self.url.scheme:
            await reject("invalid-transport", 403)
            return
        if b"authorization" in headers or b"mcp-session-id" in headers:
            await reject("credentials-and-sessions-not-supported", 400)
            return
        now = time.monotonic()
        self.calls = {
            ip: calls for ip, calls in self.calls.items() if calls and calls[-1] > now - 60
        }
        client = scope.get("client")
        ip = str(client[0]) if client else "unknown"
        if ip not in self.calls and len(self.calls) >= 1024:
            await reject("rate-limit", 429)
            return
        calls = self.calls.setdefault(ip, deque())
        while calls and calls[0] <= now - 60:
            calls.popleft()
        if len(calls) >= 60:
            await reject("rate-limit", 429)
            return
        calls.append(now)
        if scope["method"] != "POST":
            await reject("method-not-allowed", 405)
            return
        if headers.get(b"content-type", b"").split(b";")[0] != b"application/json":
            await reject("invalid-content-type", 415)
            return
        body = bytearray()
        while True:
            message = await receive()
            if message["type"] != "http.request":
                return
            chunk = message.get("body", b"")
            if len(body) + len(chunk) > MAX_REQUEST_BYTES:
                await reject("request-too-large", 413)
                return
            body.extend(chunk)
            if not message.get("more_body", False):
                break
        try:
            check_json_depth(body)
            raw = json.loads(body, object_pairs_hook=unique_object)
            rpc = types.JSONRPCMessage.model_validate(raw).root
            if isinstance(rpc, types.JSONRPCRequest):
                types.ClientRequest.model_validate(raw)
            elif isinstance(rpc, types.JSONRPCNotification):
                types.ClientNotification.model_validate(raw)
            else:
                raise ValueError("unexpected response")
            version = headers.get(b"mcp-protocol-version", PROTOCOL_VERSION.encode()).decode()
            if version != PROTOCOL_VERSION:
                raise ValueError("unsupported protocol version")
            if (
                raw.get("method") == "initialize"
                and raw["params"]["protocolVersion"] != PROTOCOL_VERSION
            ):
                raise ValueError("unsupported protocol version")
        except (ValueError, ValidationError, KeyError, TypeError, RecursionError):
            await reject("invalid-request", 400)
            return
        delivered = False

        async def replay() -> Message:
            nonlocal delivered
            if not delivered:
                delivered = True
                return {"type": "http.request", "body": bytes(body)}
            return await receive()

        await self.app(scope, replay, no_store_send)


def create_app(
    references: ReferenceSnapshot,
    public_url: str,
    *,
    loopback_http: bool = False,
) -> ASGIApp:
    logging.getLogger("mcp").setLevel(logging.CRITICAL)
    manager = StreamableHTTPSessionManager(
        create_server(references),
        stateless=True,
        json_response=True,
        max_request_body_size=MAX_REQUEST_BYTES,
    )

    @asynccontextmanager
    async def lifespan(app: Starlette) -> AsyncIterator[None]:
        async with manager.run():
            yield

    class Endpoint:
        async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
            await manager.handle_request(scope, receive, send)

    app = Starlette(routes=[Route("/mcp", endpoint=Endpoint())], lifespan=lifespan)
    return ExperimentBoundary(app, public_url, loopback_http=loopback_http)


def main() -> None:
    parser = argparse.ArgumentParser(description="Anonymous stateless MCP draft prototype")
    parser.add_argument("--resources", type=Path, required=True)
    parser.add_argument("--public-url", required=True)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--cert", type=Path)
    parser.add_argument("--key", type=Path)
    parser.add_argument("--allow-loopback-http", action="store_true")
    args = parser.parse_args()
    if args.allow_loopback_http:
        if args.host not in {"127.0.0.1", "localhost", "::1"} or args.cert or args.key:
            parser.error("HTTP tests must bind to loopback without TLS arguments")
    elif not args.cert or not args.key:
        parser.error("provide --cert and --key for HTTPS")
    try:
        app = create_app(
            ReferenceSnapshot(args.resources),
            args.public_url,
            loopback_http=args.allow_loopback_http,
        )
    except (OSError, ValueError):
        parser.error("invalid endpoint configuration or unavailable reference snapshot")
    uvicorn.run(
        app,
        host=args.host,
        port=args.port,
        access_log=False,
        log_level="critical",
        proxy_headers=False,
        ssl_certfile=str(args.cert) if args.cert else None,
        ssl_keyfile=str(args.key) if args.key else None,
    )


if __name__ == "__main__":
    main()

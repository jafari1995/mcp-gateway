from __future__ import annotations

import json
from typing import Any

import httpx

from app.models import McpServer


class UpstreamError(Exception):
    def __init__(self, message: str, status_code: int | None = None):
        super().__init__(message)
        self.status_code = status_code


def _headers(server: McpServer, session_id: str | None = None) -> dict[str, str]:
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream",
    }
    if server.auth_header:
        headers["Authorization"] = server.auth_header
    if session_id:
        headers["Mcp-Session-Id"] = session_id
    return headers


def _parse_jsonrpc_response(payload: Any) -> Any:
    if isinstance(payload, dict) and "error" in payload and payload["error"]:
        err = payload["error"]
        raise UpstreamError(str(err.get("message") or err))
    if isinstance(payload, dict):
        return payload.get("result", payload)
    return payload


def _extract_sse_json(text: str) -> Any:
    """Parse last JSON payload from an SSE body."""
    data_lines: list[str] = []
    for line in text.splitlines():
        if line.startswith("data:"):
            data_lines.append(line[5:].strip())
    if not data_lines:
        raise UpstreamError("Empty SSE response from upstream MCP")
    # Prefer the last non-empty data frame
    for raw in reversed(data_lines):
        if not raw or raw == "[DONE]":
            continue
        return json.loads(raw)
    raise UpstreamError("No JSON data frames in SSE response")


async def mcp_request(
    server: McpServer,
    method: str,
    params: dict[str, Any] | None = None,
    *,
    request_id: int = 1,
    session_id: str | None = None,
) -> tuple[Any, str | None]:
    body = {"jsonrpc": "2.0", "id": request_id, "method": method, "params": params or {}}
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            server.base_url,
            headers=_headers(server, session_id),
            json=body,
        )
        new_session = response.headers.get("mcp-session-id") or session_id
        content_type = response.headers.get("content-type", "")
        if response.status_code >= 400:
            raise UpstreamError(
                f"Upstream HTTP {response.status_code}: {response.text[:300]}",
                status_code=response.status_code,
            )
        if "text/event-stream" in content_type:
            parsed = _extract_sse_json(response.text)
        else:
            parsed = response.json()
        return _parse_jsonrpc_response(parsed), new_session


async def initialize_session(server: McpServer) -> str | None:
    result, session_id = await mcp_request(
        server,
        "initialize",
        {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "mcp-gateway", "version": "0.1.0"},
        },
        request_id=1,
    )
    # notifications/initialized (no response expected)
    async with httpx.AsyncClient(timeout=15.0) as client:
        await client.post(
            server.base_url,
            headers=_headers(server, session_id),
            json={"jsonrpc": "2.0", "method": "notifications/initialized"},
        )
    _ = result
    return session_id


async def list_tools(server: McpServer) -> list[dict[str, Any]]:
    session_id = await initialize_session(server)
    result, _ = await mcp_request(
        server,
        "tools/list",
        {},
        request_id=2,
        session_id=session_id,
    )
    tools = result.get("tools") if isinstance(result, dict) else None
    if not isinstance(tools, list):
        raise UpstreamError("Upstream tools/list did not return tools[]")
    return tools


async def call_tool(
    server: McpServer,
    name: str,
    arguments: dict[str, Any] | None = None,
) -> Any:
    session_id = await initialize_session(server)
    result, _ = await mcp_request(
        server,
        "tools/call",
        {"name": name, "arguments": arguments or {}},
        request_id=3,
        session_id=session_id,
    )
    return result

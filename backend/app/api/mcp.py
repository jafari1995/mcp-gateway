from __future__ import annotations

import json
from typing import Any

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from fastapi.responses import JSONResponse
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.db import get_db
from app.mcp_upstream import UpstreamError, call_tool
from app.models import Token, TokenToolGrant, Tool
from app.security import hash_token

router = APIRouter()


def _bearer_token(authorization: str | None) -> str:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Missing Bearer token")
    return authorization.split(" ", 1)[1].strip()


def _active_token(db: Session, raw: str) -> Token:
    token = db.scalar(
        select(Token)
        .where(Token.token_hash == hash_token(raw), Token.revoked_at.is_(None))
        .options(selectinload(Token.grants).selectinload(TokenToolGrant.tool).selectinload(Tool.server))
    )
    if not token:
        raise HTTPException(status_code=401, detail="Invalid or revoked token")
    return token


def _granted_tools(token: Token) -> list[Tool]:
    tools: list[Tool] = []
    for grant in token.grants:
        tool = grant.tool
        if tool and tool.enabled_globally:
            tools.append(tool)
    return tools


def _jsonrpc_result(request_id: Any, result: Any) -> dict[str, Any]:
    return {"jsonrpc": "2.0", "id": request_id, "result": result}


def _jsonrpc_error(request_id: Any, code: int, message: str) -> dict[str, Any]:
    return {"jsonrpc": "2.0", "id": request_id, "error": {"code": code, "message": message}}


@router.post("/mcp")
async def mcp_endpoint(
    request: Request,
    db: Session = Depends(get_db),
    authorization: str | None = Header(default=None),
) -> JSONResponse:
    raw = _bearer_token(authorization)
    token = _active_token(db, raw)

    try:
        payload = await request.json()
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=400, detail="Invalid JSON body") from exc

    # Notifications have no id; acknowledge quietly
    if isinstance(payload, dict) and payload.get("method", "").startswith("notifications/"):
        return JSONResponse(content={})

    if not isinstance(payload, dict) or "method" not in payload:
        raise HTTPException(status_code=400, detail="Expected JSON-RPC object")

    request_id = payload.get("id")
    method = payload["method"]
    params = payload.get("params") or {}

    if method == "initialize":
        return JSONResponse(
            content=_jsonrpc_result(
                request_id,
                {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {"tools": {}},
                    "serverInfo": {"name": "mcp-gateway", "version": "0.1.0"},
                },
            )
        )

    if method == "ping":
        return JSONResponse(content=_jsonrpc_result(request_id, {}))

    if method == "tools/list":
        tools = _granted_tools(token)
        listed = []
        for tool in tools:
            item: dict[str, Any] = {
                "name": tool.name,
                "description": tool.description or "",
            }
            if tool.input_schema_json:
                try:
                    item["inputSchema"] = json.loads(tool.input_schema_json)
                except json.JSONDecodeError:
                    item["inputSchema"] = {"type": "object"}
            else:
                item["inputSchema"] = {"type": "object"}
            listed.append(item)
        return JSONResponse(content=_jsonrpc_result(request_id, {"tools": listed}))

    if method == "tools/call":
        name = params.get("name")
        arguments = params.get("arguments") or {}
        if not name:
            return JSONResponse(
                content=_jsonrpc_error(request_id, -32602, "Missing tool name"),
                status_code=400,
            )
        granted = {t.name: t for t in _granted_tools(token)}
        tool = granted.get(name)
        if not tool:
            return JSONResponse(
                content=_jsonrpc_error(
                    request_id,
                    -32001,
                    f"Tool '{name}' is not granted for this token",
                ),
                status_code=403,
            )
        try:
            result = await call_tool(tool.server, name, arguments)
        except UpstreamError as exc:
            return JSONResponse(
                content=_jsonrpc_error(request_id, -32002, f"Upstream error: {exc}"),
                status_code=502,
            )
        return JSONResponse(content=_jsonrpc_result(request_id, result))

    return JSONResponse(
        content=_jsonrpc_error(request_id, -32601, f"Method not found: {method}"),
        status_code=404,
    )


@router.get("/mcp")
async def mcp_get_hint() -> dict[str, str]:
    return {
        "message": "MCP Gateway endpoint. Use JSON-RPC POST with Authorization: Bearer <token>."
    }

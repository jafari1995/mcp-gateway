from __future__ import annotations

import json

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.db import get_db
from app.deps import current_admin, current_user
from app.mcp_upstream import UpstreamError, list_tools
from app.models import McpServer, Token, TokenToolGrant, Tool, User
from app.schemas import (
    ConnectInfo,
    GrantUpdate,
    MyGatewayUpdate,
    OverviewOut,
    ServerCreate,
    ServerOut,
    TokenCreate,
    TokenOut,
    ToolOut,
    ToolPatch,
    UserCreate,
    UserOut,
)
from app.security import hash_password, hash_token, mint_token

router = APIRouter(prefix="/api")


def _server_out(server: McpServer) -> ServerOut:
    return ServerOut(
        id=server.id,
        name=server.name,
        base_url=server.base_url,
        transport=server.transport,
        status=server.status,
        last_error=server.last_error,
        is_public=server.is_public,
        created_at=server.created_at,
        tool_count=len(server.tools) if server.tools is not None else 0,
    )


def _tool_out(tool: Tool, *, granted: bool | None = None) -> ToolOut:
    return ToolOut(
        id=tool.id,
        server_id=tool.server_id,
        server_name=tool.server.name if tool.server else None,
        name=tool.name,
        description=tool.description,
        enabled_globally=tool.enabled_globally,
        granted=granted,
    )


@router.get("/overview", response_model=OverviewOut)
def overview(
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
) -> OverviewOut:
    if user.role == "admin":
        users = db.scalar(select(func.count()).select_from(User)) or 0
        tokens_active = (
            db.scalar(select(func.count()).select_from(Token).where(Token.revoked_at.is_(None)))
            or 0
        )
        servers = db.scalar(select(func.count()).select_from(McpServer)) or 0
        tools = db.scalar(select(func.count()).select_from(Tool)) or 0
        needs_setup = servers == 0
    else:
        users = 1
        tokens_active = (
            db.scalar(
                select(func.count())
                .select_from(Token)
                .where(Token.user_id == user.id, Token.revoked_at.is_(None))
            )
            or 0
        )
        servers = (
            db.scalar(select(func.count()).select_from(McpServer).where(McpServer.is_public.is_(True)))
            or 0
        )
        tools = db.scalar(select(func.count()).select_from(Tool).where(Tool.enabled_globally.is_(True))) or 0
        needs_setup = tokens_active == 0
    return OverviewOut(
        users=users,
        tokens_active=tokens_active,
        servers=servers,
        tools=tools,
        needs_setup=needs_setup,
        me=UserOut.model_validate(user),
    )


@router.get("/connect", response_model=ConnectInfo)
def connect_info(request: Request, user: User = Depends(current_user)) -> ConnectInfo:
    # Prefer public URL when behind the Next proxy UI.
    base = str(request.base_url).rstrip("/")
    # If request came via frontend proxy Host may be frontend; expose localhost gateway for clients.
    mcp_url = "http://localhost:8000/mcp"
    snippet = {
        "mcpServers": {
            "mcp-gateway": {
                "url": mcp_url,
                "headers": {"Authorization": "Bearer YOUR_PLATFORM_TOKEN"},
            }
        }
    }
    return ConnectInfo(
        mcp_url=mcp_url,
        example_cursor_snippet=json.dumps(snippet, indent=2),
        hint=f"کاربر {user.username}: ابتدا در صفحه Gateway ابزارها را انتخاب و token بسازید.",
    )


# ---------- Admin: users ----------


@router.get("/users", response_model=list[UserOut])
def list_users(
    db: Session = Depends(get_db),
    _: User = Depends(current_admin),
) -> list[User]:
    return list(db.scalars(select(User).order_by(User.id)).all())


@router.post("/users", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def create_user(
    payload: UserCreate,
    db: Session = Depends(get_db),
    _: User = Depends(current_admin),
) -> User:
    username = payload.username.strip().lower()
    if db.scalar(select(User).where(User.username == username)):
        raise HTTPException(status_code=400, detail="این نام کاربری قبلاً ثبت شده است")
    if db.scalar(select(User).where(User.email == payload.email.strip())):
        raise HTTPException(status_code=400, detail="این ایمیل قبلاً ثبت شده است")
    role = payload.role if payload.role in {"admin", "user"} else "user"
    user = User(
        name=payload.name.strip(),
        username=username,
        email=payload.email.strip(),
        password_hash=hash_password(payload.password),
        role=role,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


# ---------- Me: tokens + gateway builder ----------


@router.get("/me/tokens", response_model=list[TokenOut])
def my_tokens(db: Session = Depends(get_db), user: User = Depends(current_user)) -> list[TokenOut]:
    tokens = db.scalars(
        select(Token).where(Token.user_id == user.id).order_by(Token.id.desc())
    ).all()
    return [
        TokenOut(
            id=t.id,
            user_id=t.user_id,
            label=t.label,
            token_prefix=t.token_prefix,
            created_at=t.created_at,
            revoked_at=t.revoked_at,
        )
        for t in tokens
    ]


@router.post("/me/tokens", response_model=TokenOut, status_code=status.HTTP_201_CREATED)
def create_my_token(
    payload: TokenCreate,
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
) -> TokenOut:
    raw = mint_token()
    token = Token(
        user_id=user.id,
        label=payload.label,
        token_hash=hash_token(raw),
        token_prefix=raw[:12],
    )
    db.add(token)
    db.flush()
    for tool_id in payload.tool_ids:
        tool = db.get(Tool, tool_id)
        if not tool or not tool.enabled_globally:
            raise HTTPException(status_code=400, detail=f"Tool {tool_id} معتبر نیست")
        db.add(TokenToolGrant(token_id=token.id, tool_id=tool_id))
    db.commit()
    db.refresh(token)
    return TokenOut(
        id=token.id,
        user_id=token.user_id,
        label=token.label,
        token_prefix=token.token_prefix,
        created_at=token.created_at,
        revoked_at=token.revoked_at,
        raw_token=raw,
    )


@router.post("/me/gateway", response_model=TokenOut, status_code=status.HTTP_201_CREATED)
def build_my_gateway(
    payload: MyGatewayUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
) -> TokenOut:
    """One-shot: create platform token with selected tools from catalog."""
    if not payload.tool_ids:
        raise HTTPException(status_code=400, detail="حداقل یک tool انتخاب کنید")
    return create_my_token(
        TokenCreate(label=payload.label, tool_ids=payload.tool_ids),
        db,
        user,
    )


@router.post("/me/tokens/{token_id}/revoke", response_model=TokenOut)
def revoke_my_token(
    token_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
) -> TokenOut:
    from datetime import datetime, timezone

    token = db.get(Token, token_id)
    if not token or token.user_id != user.id:
        raise HTTPException(status_code=404, detail="Token پیدا نشد")
    token.revoked_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(token)
    return TokenOut(
        id=token.id,
        user_id=token.user_id,
        label=token.label,
        token_prefix=token.token_prefix,
        created_at=token.created_at,
        revoked_at=token.revoked_at,
    )


@router.get("/me/tokens/{token_id}/grants", response_model=list[ToolOut])
def my_grants(
    token_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
) -> list[ToolOut]:
    token = db.get(Token, token_id)
    if not token or token.user_id != user.id:
        raise HTTPException(status_code=404, detail="Token پیدا نشد")
    granted_ids = {
        g.tool_id
        for g in db.scalars(select(TokenToolGrant).where(TokenToolGrant.token_id == token_id))
    }
    tools = db.scalars(
        select(Tool).options(selectinload(Tool.server)).order_by(Tool.server_id, Tool.name)
    ).all()
    return [_tool_out(t, granted=t.id in granted_ids) for t in tools]


@router.put("/me/tokens/{token_id}/grants", response_model=list[ToolOut])
def set_my_grants(
    token_id: int,
    payload: GrantUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
) -> list[ToolOut]:
    token = db.get(Token, token_id)
    if not token or token.user_id != user.id:
        raise HTTPException(status_code=404, detail="Token پیدا نشد")
    if token.revoked_at is not None:
        raise HTTPException(status_code=400, detail="token باطل‌شده قابل ویرایش نیست")
    if not payload.tool_ids:
        raise HTTPException(status_code=400, detail="حداقل یک tool انتخاب کنید")
    existing = list(
        db.scalars(select(TokenToolGrant).where(TokenToolGrant.token_id == token_id))
    )
    for g in existing:
        db.delete(g)
    db.flush()
    for tool_id in dict.fromkeys(payload.tool_ids):
        tool = db.get(Tool, tool_id)
        if not tool or not tool.enabled_globally:
            raise HTTPException(status_code=400, detail=f"Tool {tool_id} معتبر نیست")
        db.add(TokenToolGrant(token_id=token_id, tool_id=tool_id))
    db.commit()
    return my_grants(token_id, db, user)


@router.get("/catalog/tools", response_model=list[ToolOut])
def catalog_tools(
    db: Session = Depends(get_db),
    _: User = Depends(current_user),
) -> list[ToolOut]:
    tools = db.scalars(
        select(Tool)
        .join(McpServer)
        .where(McpServer.is_public.is_(True), Tool.enabled_globally.is_(True))
        .options(selectinload(Tool.server))
        .order_by(McpServer.name, Tool.name)
    ).all()
    return [_tool_out(t) for t in tools]


# ---------- Servers catalog ----------


@router.get("/servers", response_model=list[ServerOut])
def list_servers(
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
) -> list[ServerOut]:
    q = select(McpServer).options(selectinload(McpServer.tools)).order_by(McpServer.id)
    if user.role != "admin":
        q = q.where(McpServer.is_public.is_(True))
    servers = db.scalars(q).all()
    return [_server_out(s) for s in servers]


@router.post("/servers/demo", response_model=ServerOut, status_code=status.HTTP_201_CREATED)
def create_demo_server(
    db: Session = Depends(get_db),
    _: User = Depends(current_admin),
) -> ServerOut:
    from app.config import get_settings

    existing = db.scalar(select(McpServer).where(McpServer.name == "demo-mcp"))
    if existing:
        existing = db.scalar(
            select(McpServer)
            .where(McpServer.id == existing.id)
            .options(selectinload(McpServer.tools))
        )
        assert existing is not None
        return _server_out(existing)
    settings = get_settings()
    server = McpServer(
        name="demo-mcp",
        base_url=settings.demo_mcp_url.rstrip("/"),
        transport="streamable-http",
        status="registered",
        is_public=True,
    )
    db.add(server)
    db.commit()
    db.refresh(server)
    server.tools = []
    return _server_out(server)


@router.post("/servers", response_model=ServerOut, status_code=status.HTTP_201_CREATED)
def create_server(
    payload: ServerCreate,
    db: Session = Depends(get_db),
    _: User = Depends(current_admin),
) -> ServerOut:
    if not payload.name.strip() or not payload.base_url.strip():
        raise HTTPException(status_code=400, detail="name و base_url الزامی است")
    if db.scalar(select(McpServer).where(McpServer.name == payload.name.strip())):
        raise HTTPException(
            status_code=400,
            detail="این نام قبلاً ثبت شده. برای MCP جدید یک نام یکتا بگذارید.",
        )
    server = McpServer(
        name=payload.name.strip(),
        base_url=payload.base_url.strip().rstrip("/"),
        transport=payload.transport,
        auth_header=payload.auth_header,
        status="registered",
        is_public=True,
    )
    db.add(server)
    db.commit()
    db.refresh(server)
    server.tools = []
    return _server_out(server)


@router.delete("/servers/{server_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_server(
    server_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(current_admin),
) -> None:
    server = db.get(McpServer, server_id)
    if not server:
        raise HTTPException(status_code=404, detail="Server پیدا نشد")
    db.delete(server)
    db.commit()


@router.post("/servers/{server_id}/sync", response_model=ServerOut)
async def sync_server(
    server_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(current_admin),
) -> ServerOut:
    server = db.scalar(
        select(McpServer)
        .where(McpServer.id == server_id)
        .options(selectinload(McpServer.tools))
    )
    if not server:
        raise HTTPException(status_code=404, detail="Server پیدا نشد")
    try:
        remote_tools = await list_tools(server)
        by_name = {t.name: t for t in server.tools}
        seen: set[str] = set()
        for item in remote_tools:
            name = item.get("name")
            if not name:
                continue
            seen.add(name)
            schema = item.get("inputSchema") or item.get("input_schema")
            schema_json = json.dumps(schema) if schema is not None else None
            if name in by_name:
                tool = by_name[name]
                tool.description = item.get("description")
                tool.input_schema_json = schema_json
            else:
                db.add(
                    Tool(
                        server_id=server.id,
                        name=name,
                        description=item.get("description"),
                        input_schema_json=schema_json,
                        enabled_globally=True,
                    )
                )
        for name, tool in by_name.items():
            if name not in seen:
                db.delete(tool)
        server.status = "online"
        server.last_error = None
        db.commit()
    except UpstreamError as exc:
        server.status = "error"
        server.last_error = str(exc)
        db.commit()
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    server = db.scalar(
        select(McpServer)
        .where(McpServer.id == server_id)
        .options(selectinload(McpServer.tools))
    )
    assert server is not None
    return _server_out(server)


@router.get("/servers/{server_id}/tools", response_model=list[ToolOut])
def server_tools(
    server_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(current_user),
) -> list[ToolOut]:
    server = db.get(McpServer, server_id)
    if not server:
        raise HTTPException(status_code=404, detail="Server پیدا نشد")
    tools = db.scalars(
        select(Tool)
        .where(Tool.server_id == server_id)
        .options(selectinload(Tool.server))
        .order_by(Tool.name)
    ).all()
    return [_tool_out(t) for t in tools]


@router.get("/tools", response_model=list[ToolOut])
def all_tools(
    db: Session = Depends(get_db),
    _: User = Depends(current_user),
) -> list[ToolOut]:
    return catalog_tools(db, _)


@router.patch("/tools/{tool_id}", response_model=ToolOut)
def patch_tool(
    tool_id: int,
    payload: ToolPatch,
    db: Session = Depends(get_db),
    _: User = Depends(current_admin),
) -> ToolOut:
    tool = db.scalar(
        select(Tool).where(Tool.id == tool_id).options(selectinload(Tool.server))
    )
    if not tool:
        raise HTTPException(status_code=404, detail="Tool پیدا نشد")
    if payload.enabled_globally is not None:
        tool.enabled_globally = payload.enabled_globally
    db.commit()
    db.refresh(tool)
    return _tool_out(tool)

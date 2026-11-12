from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    username: str = Field(min_length=1, max_length=80)
    password: str = Field(min_length=1, max_length=200)


class LoginResponse(BaseModel):
    ok: bool
    session_token: str
    user: "UserOut"


class UserCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    username: str = Field(min_length=3, max_length=80)
    email: str = Field(min_length=3, max_length=255)
    password: str = Field(min_length=4, max_length=200)
    role: str = "user"


class UserOut(BaseModel):
    id: int
    name: str
    username: str
    email: str
    role: str
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class TokenCreate(BaseModel):
    label: str = "default"
    tool_ids: list[int] = Field(default_factory=list)


class TokenOut(BaseModel):
    id: int
    user_id: int
    label: str
    token_prefix: str
    created_at: datetime
    revoked_at: datetime | None
    raw_token: str | None = None

    model_config = {"from_attributes": True}


class ServerCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    base_url: str = Field(min_length=1, max_length=500)
    transport: str = "streamable-http"
    auth_header: str | None = None


class ServerOut(BaseModel):
    id: int
    name: str
    base_url: str
    transport: str
    status: str
    last_error: str | None
    is_public: bool = True
    created_at: datetime
    tool_count: int = 0

    model_config = {"from_attributes": True}


class ToolOut(BaseModel):
    id: int
    server_id: int
    server_name: str | None = None
    name: str
    description: str | None
    enabled_globally: bool
    granted: bool | None = None
    selected: bool | None = None

    model_config = {"from_attributes": True}


class ToolPatch(BaseModel):
    enabled_globally: bool | None = None


class GrantUpdate(BaseModel):
    tool_ids: list[int]


class MyGatewayUpdate(BaseModel):
    """User builds their gateway by selecting tools from the catalog."""

    label: str = "my-gateway"
    tool_ids: list[int]


class OverviewOut(BaseModel):
    users: int
    tokens_active: int
    servers: int
    tools: int
    needs_setup: bool
    me: UserOut | None = None


class ConnectInfo(BaseModel):
    mcp_url: str
    example_cursor_snippet: str
    hint: str

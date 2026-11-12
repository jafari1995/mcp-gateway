from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120))
    username: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(200))
    role: Mapped[str] = mapped_column(String(20), default="user")  # admin | user
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    session_token_hash: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    tokens: Mapped[list[Token]] = relationship(back_populates="user", cascade="all, delete-orphan")


class Token(Base):
    __tablename__ = "tokens"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    label: Mapped[str] = mapped_column(String(120), default="default")
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    token_prefix: Mapped[str] = mapped_column(String(16))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    user: Mapped[User] = relationship(back_populates="tokens")
    grants: Mapped[list[TokenToolGrant]] = relationship(
        back_populates="token", cascade="all, delete-orphan"
    )


class McpServer(Base):
    __tablename__ = "mcp_servers"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120), unique=True)
    base_url: Mapped[str] = mapped_column(String(500))
    transport: Mapped[str] = mapped_column(String(40), default="streamable-http")
    auth_header: Mapped[str | None] = mapped_column(String(500), nullable=True)
    status: Mapped[str] = mapped_column(String(40), default="unknown")
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_public: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    tools: Mapped[list[Tool]] = relationship(back_populates="server", cascade="all, delete-orphan")


class Tool(Base):
    __tablename__ = "tools"
    __table_args__ = (UniqueConstraint("server_id", "name", name="uq_server_tool"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    server_id: Mapped[int] = mapped_column(ForeignKey("mcp_servers.id", ondelete="CASCADE"))
    name: Mapped[str] = mapped_column(String(200))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    input_schema_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    enabled_globally: Mapped[bool] = mapped_column(Boolean, default=True)

    server: Mapped[McpServer] = relationship(back_populates="tools")
    grants: Mapped[list[TokenToolGrant]] = relationship(
        back_populates="tool", cascade="all, delete-orphan"
    )


class TokenToolGrant(Base):
    __tablename__ = "token_tool_grants"
    __table_args__ = (UniqueConstraint("token_id", "tool_id", name="uq_token_tool"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    token_id: Mapped[int] = mapped_column(ForeignKey("tokens.id", ondelete="CASCADE"))
    tool_id: Mapped[int] = mapped_column(ForeignKey("tools.id", ondelete="CASCADE"))

    token: Mapped[Token] = relationship(back_populates="grants")
    tool: Mapped[Tool] = relationship(back_populates="grants")

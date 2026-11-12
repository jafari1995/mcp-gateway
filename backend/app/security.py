from __future__ import annotations

import hashlib
import hmac
import secrets

from fastapi import Header, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.models import User


def hash_token(raw: str) -> str:
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def hash_password(password: str) -> str:
    # Demo-grade salted hash (enough for thesis demo; not Argon2).
    salt = secrets.token_hex(16)
    digest = hashlib.sha256(f"{salt}:{password}".encode("utf-8")).hexdigest()
    return f"{salt}${digest}"


def verify_password(password: str, password_hash: str) -> bool:
    try:
        salt, digest = password_hash.split("$", 1)
    except ValueError:
        return False
    check = hashlib.sha256(f"{salt}:{password}".encode("utf-8")).hexdigest()
    return hmac.compare_digest(check, digest)


def mint_token() -> str:
    settings = get_settings()
    return f"{settings.token_prefix}{secrets.token_urlsafe(24)}"


def mint_session_token() -> str:
    return f"sess_{secrets.token_urlsafe(32)}"


def get_user_by_session(db: Session, authorization: str | None) -> User:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="نشست نامعتبر است. دوباره وارد شوید.",
        )
    raw = authorization.split(" ", 1)[1].strip()
    user = db.scalar(
        select(User).where(
            User.session_token_hash == hash_token(raw),
            User.is_active.is_(True),
        )
    )
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="نشست منقضی یا نامعتبر است.",
        )
    return user


def require_admin_user(user: User) -> None:
    if user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="فقط ادمین به این بخش دسترسی دارد.",
        )


# Kept for optional scripts / health tooling that still send X-Admin-Key
def require_admin(x_admin_key: str | None = Header(default=None)) -> None:
    settings = get_settings()
    if not x_admin_key or x_admin_key != settings.admin_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing X-Admin-Key",
        )

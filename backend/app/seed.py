from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.models import User
from app.security import hash_password


def ensure_admin_user(db: Session) -> None:
    settings = get_settings()
    existing = db.scalar(select(User).where(User.username == settings.admin_username))
    if existing:
        return
    admin = User(
        name="Administrator",
        username=settings.admin_username,
        email=f"{settings.admin_username}@local",
        password_hash=hash_password(settings.admin_api_key),
        role="admin",
        is_active=True,
    )
    db.add(admin)
    db.commit()

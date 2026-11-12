from __future__ import annotations

from fastapi import Depends, Header
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import User
from app.security import get_user_by_session, require_admin_user


def current_user(
    db: Session = Depends(get_db),
    authorization: str | None = Header(default=None),
) -> User:
    return get_user_by_session(db, authorization)


def current_admin(user: User = Depends(current_user)) -> User:
    require_admin_user(user)
    return user

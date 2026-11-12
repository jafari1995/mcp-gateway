from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.deps import current_user
from app.models import User
from app.schemas import LoginRequest, LoginResponse, UserOut
from app.security import (
    hash_token,
    mint_session_token,
    verify_password,
)

router = APIRouter(prefix="/api/auth")


@router.post("/login", response_model=LoginResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> LoginResponse:
    user = db.scalar(select(User).where(User.username == payload.username.strip()))
    if (
        not user
        or not user.is_active
        or not verify_password(payload.password, user.password_hash)
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="نام کاربری یا رمز عبور نادرست است",
        )
    raw = mint_session_token()
    user.session_token_hash = hash_token(raw)
    db.commit()
    db.refresh(user)
    return LoginResponse(ok=True, session_token=raw, user=UserOut.model_validate(user))


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(current_user)) -> User:
    return user


@router.post("/logout")
def logout(user: User = Depends(current_user), db: Session = Depends(get_db)) -> dict[str, bool]:
    user.session_token_hash = None
    db.commit()
    return {"ok": True}

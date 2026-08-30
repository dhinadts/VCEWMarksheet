import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.core.security import create_access_token, create_refresh_token, decode_token, hash_password, token_fingerprint, verify_password
from app.models.models import RefreshToken, User, UserType
from app.schemas.auth import ChangePasswordRequest, LoginRequest, LogoutRequest, RefreshRequest
from app.schemas.common import ok

router = APIRouter()


def issue_tokens(db: Session, user: User) -> dict:
    access = create_access_token(str(user.id), user.user_type.value)
    refresh, jti, expires = create_refresh_token(str(user.id))
    db.add(RefreshToken(user_id=user.id, jti=jti, token_hash=token_fingerprint(refresh), expires_at=expires))
    db.commit()
    return {"access_token": access, "refresh_token": refresh, "token_type": "bearer", "must_change_password": user.must_change_password}


@router.post("/login")
def login(body: LoginRequest, db: Session = Depends(get_db)):
    identifier = body.username.strip()
    user = db.scalar(select(User).where((User.username == identifier) | (User.email == identifier.lower())))
    if not user or not verify_password(body.password, user.password_hash) or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail={"code": "INVALID_CREDENTIALS", "message": "Invalid username or password"})
    if user.user_type == UserType.STUDENT:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail={"code": "STAFF_LOGIN_ONLY", "message": "Students can view marks using their roll number on the web student portal"})
    user.last_login_at = datetime.now(UTC)
    db.add(user)
    db.commit()
    return ok(issue_tokens(db, user), "Login successful")


@router.post("/refresh")
def refresh(body: RefreshRequest, db: Session = Depends(get_db)):
    try:
        payload = decode_token(body.refresh_token, "refresh")
    except ValueError:
        raise HTTPException(status_code=401, detail={"code": "INVALID_REFRESH_TOKEN", "message": "Invalid or expired refresh token"})
    stored = db.scalar(select(RefreshToken).where(RefreshToken.jti == payload["jti"], RefreshToken.token_hash == token_fingerprint(body.refresh_token)))
    now = datetime.now(UTC)
    if not stored or stored.revoked_at or stored.expires_at.replace(tzinfo=stored.expires_at.tzinfo or UTC) <= now:
        raise HTTPException(status_code=401, detail={"code": "REVOKED_REFRESH_TOKEN", "message": "Refresh token is unavailable"})
    stored.revoked_at = now
    user = db.get(User, uuid.UUID(payload["sub"]))
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail={"code": "INACTIVE_USER", "message": "User is inactive"})
    db.add(stored)
    db.commit()
    return ok(issue_tokens(db, user), "Token refreshed")


@router.post("/logout")
def logout(body: LogoutRequest, db: Session = Depends(get_db)):
    stored = db.scalar(select(RefreshToken).where(RefreshToken.token_hash == token_fingerprint(body.refresh_token)))
    if stored and not stored.revoked_at:
        stored.revoked_at = datetime.now(UTC)
        db.commit()
    return ok({}, "Logout successful")


@router.post("/change-password")
def change_password(body: ChangePasswordRequest, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if not verify_password(body.current_password, user.password_hash):
        raise HTTPException(status_code=400, detail={"code": "INVALID_CURRENT_PASSWORD", "message": "Current password is incorrect"})
    user.password_hash = hash_password(body.new_password)
    user.must_change_password = False
    db.query(RefreshToken).filter(RefreshToken.user_id == user.id, RefreshToken.revoked_at.is_(None)).update({"revoked_at": datetime.now(UTC)})
    db.commit()
    return ok({}, "Password changed successfully")


@router.get("/me")
def me(user: User = Depends(get_current_user)):
    return ok({"id": str(user.id), "username": user.username, "email": user.email, "user_type": user.user_type.value, "must_change_password": user.must_change_password})

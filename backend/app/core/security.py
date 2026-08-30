import hashlib
import secrets
from datetime import UTC, datetime, timedelta
from typing import Any

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import get_settings

pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")
ALGORITHM = "HS256"


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    return pwd_context.verify(password, password_hash)


def create_access_token(subject: str, user_type: str) -> str:
    settings = get_settings()
    now = datetime.now(UTC)
    return jwt.encode(
        {"sub": subject, "type": "access", "role": user_type, "iat": now, "exp": now + timedelta(minutes=settings.access_token_expire_minutes)},
        settings.secret_key,
        algorithm=ALGORITHM,
    )


def create_refresh_token(subject: str) -> tuple[str, str, datetime]:
    settings = get_settings()
    now = datetime.now(UTC)
    jti = secrets.token_urlsafe(32)
    expires = now + timedelta(days=settings.refresh_token_expire_days)
    token = jwt.encode({"sub": subject, "type": "refresh", "jti": jti, "iat": now, "exp": expires}, settings.secret_key, algorithm=ALGORITHM)
    return token, jti, expires


def decode_token(token: str, expected_type: str) -> dict[str, Any]:
    try:
        payload = jwt.decode(token, get_settings().secret_key, algorithms=[ALGORITHM])
    except JWTError as exc:
        raise ValueError("Invalid or expired token") from exc
    if payload.get("type") != expected_type or not payload.get("sub"):
        raise ValueError("Invalid token type")
    return payload


def token_fingerprint(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()

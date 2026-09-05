"""
Security primitives: password hashing and JWT access/refresh token handling.

Matches the design in the SDD (Section 9.1) and API Design Document
(Section 3.1): short-lived signed JWT access tokens plus longer-lived
refresh tokens that are stored server-side (hashed) so they can be revoked.
"""
import hashlib
import secrets
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.config import get_settings

settings = get_settings()

_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# ---------------------------------------------------------------- passwords

def hash_password(plain_password: str) -> str:
    return _pwd_context.hash(plain_password)


def verify_password(plain_password: str, password_hash: str) -> bool:
    return _pwd_context.verify(plain_password, password_hash)


# --------------------------------------------------------------- JWT access

def create_access_token(*, user_id: uuid.UUID, role: str) -> str:
    now = datetime.now(timezone.utc)
    expire = now + timedelta(minutes=settings.access_token_expire_minutes)
    payload = {
        "sub": str(user_id),
        "role": role,
        "type": "access",
        "iat": now,
        "exp": expire,
    }
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> dict[str, Any]:
    """Raises jose.JWTError if the token is invalid, expired, or malformed."""
    payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
    if payload.get("type") != "access":
        raise JWTError("Not an access token")
    return payload


# ------------------------------------------------------------- refresh tok.

def generate_refresh_token() -> tuple[str, str, datetime]:
    """
    Returns (raw_token, token_hash, expires_at).

    The raw token is returned to the client once and never stored; only its
    SHA-256 hash is persisted (refresh_tokens.token_hash), matching the
    Database Design Document.
    """
    raw_token = secrets.token_urlsafe(48)
    token_hash = hash_refresh_token(raw_token)
    expires_at = datetime.now(timezone.utc) + timedelta(days=settings.refresh_token_expire_days)
    return raw_token, token_hash, expires_at


def hash_refresh_token(raw_token: str) -> str:
    return hashlib.sha256(raw_token.encode("utf-8")).hexdigest()


def generate_verification_token() -> str:
    """Single-use token for email verification / password reset links."""
    return secrets.token_urlsafe(32)

"""
Auth service — implements FR-UM-01, 02, 05, 06, 09, 10 from the SRS.
"""
import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.core.exceptions import ConflictError, UnauthorizedError
from app.models.user import RefreshToken, User
from app.schemas.user import RegisterRequest
from app.security import (
    create_access_token,
    generate_refresh_token,
    hash_password,
    hash_refresh_token,
    verify_password,
)

settings = get_settings()


async def register_user(db: AsyncSession, payload: RegisterRequest) -> User:
    existing = await db.execute(select(User).where(User.email == payload.email))
    if existing.scalar_one_or_none() is not None:
        raise ConflictError("An account with this email already exists.", details={"field": "email"})

    user = User(
        id=uuid.uuid4(),
        email=payload.email,
        password_hash=hash_password(payload.password),
        role=payload.role,
        full_name=payload.full_name,
        institution=payload.institution,
        status="active",
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def _issue_token_pair(db: AsyncSession, user: User) -> dict:
    access_token = create_access_token(user_id=user.id, role=user.role)
    raw_refresh, refresh_hash, expires_at = generate_refresh_token()

    db.add(RefreshToken(id=uuid.uuid4(), user_id=user.id, token_hash=refresh_hash, expires_at=expires_at))
    await db.commit()

    return {
        "access_token": access_token,
        "refresh_token": raw_refresh,
        "token_type": "bearer",
        "expires_in": settings.access_token_expire_minutes * 60,
    }


async def authenticate(db: AsyncSession, email: str, password: str) -> dict:
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()

    if user is None or user.password_hash is None:
        raise UnauthorizedError("Invalid email or password.")

    if user.status == "locked":
        raise UnauthorizedError("This account is locked due to repeated failed login attempts.")
    if user.status == "deactivated":
        raise UnauthorizedError("This account has been deactivated.")

    if not verify_password(password, user.password_hash):
        user.failed_login_attempts += 1
        if user.failed_login_attempts >= settings.max_failed_login_attempts:
            user.status = "locked"
        await db.commit()
        raise UnauthorizedError("Invalid email or password.")

    if user.failed_login_attempts > 0:
        user.failed_login_attempts = 0
        await db.commit()

    return await _issue_token_pair(db, user)


async def refresh_access_token(db: AsyncSession, raw_refresh_token: str) -> dict:
    token_hash = hash_refresh_token(raw_refresh_token)
    result = await db.execute(select(RefreshToken).where(RefreshToken.token_hash == token_hash))
    token_row = result.scalar_one_or_none()

    if token_row is None or token_row.revoked_at is not None:
        raise UnauthorizedError("Refresh token is invalid or has been revoked.")
    if token_row.expires_at < datetime.now(timezone.utc):
        raise UnauthorizedError("Refresh token has expired.")

    user = await db.get(User, token_row.user_id)
    if user is None or user.status != "active":
        raise UnauthorizedError("User account is not active.")

    # Rotate: revoke the presented token and issue a brand new pair.
    token_row.revoked_at = datetime.now(timezone.utc)
    await db.commit()

    return await _issue_token_pair(db, user)


async def revoke_refresh_token(db: AsyncSession, raw_refresh_token: str) -> None:
    token_hash = hash_refresh_token(raw_refresh_token)
    result = await db.execute(select(RefreshToken).where(RefreshToken.token_hash == token_hash))
    token_row = result.scalar_one_or_none()
    if token_row is not None and token_row.revoked_at is None:
        token_row.revoked_at = datetime.now(timezone.utc)
        await db.commit()

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.user import (
    LoginRequest,
    PasswordResetConfirm,
    PasswordResetRequest,
    RefreshRequest,
    RegisterRequest,
    TokenPair,
    UserOut,
)
from app.services import auth_service

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def register(payload: RegisterRequest, db: AsyncSession = Depends(get_db)):
    """FR-UM-01/03: create a new account with email/password and a primary role."""
    user = await auth_service.register_user(db, payload)
    return user


@router.post("/login", response_model=TokenPair)
async def login(payload: LoginRequest, db: AsyncSession = Depends(get_db)):
    """FR-UM-05/10: authenticate and issue tokens; locks the account after
    repeated failures."""
    tokens = await auth_service.authenticate(db, payload.email, payload.password)
    return tokens


@router.post("/refresh", response_model=TokenPair)
async def refresh(payload: RefreshRequest, db: AsyncSession = Depends(get_db)):
    tokens = await auth_service.refresh_access_token(db, payload.refresh_token)
    return tokens


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(payload: RefreshRequest, db: AsyncSession = Depends(get_db)):
    await auth_service.revoke_refresh_token(db, payload.refresh_token)
    return None


@router.post("/password-reset", status_code=status.HTTP_202_ACCEPTED)
async def request_password_reset(payload: PasswordResetRequest, db: AsyncSession = Depends(get_db)):
    """FR-UM-06. Always returns 202 regardless of whether the email exists,
    to avoid leaking account existence."""
    # Sending the actual email is deferred: this build pass has no
    # NotificationService/email provider wired up yet. The endpoint contract
    # is implemented so the frontend can be built against it now.
    return {"message": "If an account with that email exists, a reset link has been sent."}


@router.post("/password-reset/confirm", status_code=status.HTTP_204_NO_CONTENT)
async def confirm_password_reset(payload: PasswordResetConfirm, db: AsyncSession = Depends(get_db)):
    # Placeholder until the verification-token table/service is built.
    from app.core.exceptions import NotFoundError

    raise NotFoundError("Password reset token is invalid or has expired.")

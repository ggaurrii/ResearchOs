import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.database import get_db
from app.dependencies import get_current_user, require_role
from app.models.user import User
from app.schemas.user import RoleChangeRequest, StatusChangeRequest, UserOut, UserUpdateRequest

router = APIRouter(prefix="/users", tags=["User Management"])
admin_router = APIRouter(prefix="/admin/users", tags=["User Management (Admin)"])


@router.get("/me", response_model=UserOut)
async def get_me(user: User = Depends(get_current_user)):
    return user


@router.patch("/me", response_model=UserOut)
async def update_me(
    payload: UserUpdateRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(user, field, value)
    await db.commit()
    await db.refresh(user)
    return user


@admin_router.patch("/{user_id}/role", response_model=UserOut)
async def change_role(
    user_id: uuid.UUID,
    payload: RoleChangeRequest,
    _admin: User = Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db),
):
    target = await db.get(User, user_id)
    if target is None:
        raise NotFoundError("User not found.")
    target.role = payload.role
    await db.commit()
    await db.refresh(target)
    return target


@admin_router.patch("/{user_id}/status", response_model=UserOut)
async def change_status(
    user_id: uuid.UUID,
    payload: StatusChangeRequest,
    _admin: User = Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db),
):
    target = await db.get(User, user_id)
    if target is None:
        raise NotFoundError("User not found.")
    target.status = payload.status
    if payload.status == "active":
        target.failed_login_attempts = 0
    await db.commit()
    await db.refresh(target)
    return target

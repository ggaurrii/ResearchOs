"""
Shared FastAPI dependencies: current-user resolution and the Member/Owner
authorization checks used throughout the API, matching the auth labels
defined in the API Design Document, Section 3.3.
"""
import uuid
from typing import Optional

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ForbiddenError, NotFoundError, UnauthorizedError
from app.database import get_db
from app.models.user import User
from app.models.workspace import Workspace, WorkspaceMember
from app.security import decode_access_token
bearer_scheme = HTTPBearer()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:

    token = credentials.credentials
    try:
        payload = decode_access_token(token)
    except JWTError:
        raise UnauthorizedError("Invalid or expired access token.")

    user_id = payload.get("sub")
    try:
        user_uuid = uuid.UUID(user_id)
    except (TypeError, ValueError):
        raise UnauthorizedError("Invalid token subject.")

    user = await db.get(User, user_uuid)
    if user is None:
        raise UnauthorizedError("User associated with this token no longer exists.")
    if user.status != "active":
        raise ForbiddenError(f"Account is {user.status}.")

    return user


def require_role(*roles: str):
    async def _check(user: User = Depends(get_current_user)) -> User:
        if user.role not in roles:
            raise ForbiddenError(f"This action requires one of roles: {', '.join(roles)}.")
        return user

    return _check


async def get_workspace_or_404(workspace_id: uuid.UUID, db: AsyncSession = Depends(get_db)) -> Workspace:
    workspace = await db.get(Workspace, workspace_id)
    if workspace is None or workspace.status == "deleted":
        raise NotFoundError("Workspace not found.")
    return workspace


async def require_workspace_member(
    workspace: Workspace = Depends(get_workspace_or_404),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Workspace:
    if workspace.visibility == "public":
        return workspace  # public workspaces are readable by any authenticated user

    result = await db.execute(
        select(WorkspaceMember).where(
            WorkspaceMember.workspace_id == workspace.id, WorkspaceMember.user_id == user.id
        )
    )
    if result.scalar_one_or_none() is None:
        raise ForbiddenError("You are not a member of this workspace.")
    return workspace


async def require_workspace_owner(
    workspace: Workspace = Depends(get_workspace_or_404),
    user: User = Depends(get_current_user),
) -> Workspace:
    if workspace.owner_id != user.id and user.role != "admin":
        raise ForbiddenError("Only the workspace owner may perform this action.")
    return workspace

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.pagination import Page, PageParams
from app.database import get_db
from app.dependencies import get_current_user, require_workspace_member, require_workspace_owner
from app.models.user import User
from app.models.workspace import Workspace
from app.schemas.workspace import (
    ActivityLogOut,
    WorkspaceCreateRequest,
    WorkspaceOut,
    WorkspaceUpdateRequest,
)
from app.services import workspace_service

router = APIRouter(prefix="/workspaces", tags=["Research Workspace"])


@router.post("", response_model=WorkspaceOut, status_code=201)
async def create_workspace(
    payload: WorkspaceCreateRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """FR-RW-01: create a new project workspace."""
    return await workspace_service.create_workspace(db, user, payload)


@router.get("", response_model=Page[WorkspaceOut])
async def list_my_workspaces(
    params: PageParams = Depends(),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    rows, total = await workspace_service.list_my_workspaces(db, user, params.offset, params.page_size)
    return Page(results=rows, page=params.page, page_size=params.page_size, total_results=total)


@router.get("/{workspace_id}", response_model=WorkspaceOut)
async def get_workspace(workspace: Workspace = Depends(require_workspace_member)):
    return workspace


@router.patch("/{workspace_id}", response_model=WorkspaceOut)
async def update_workspace(
    payload: WorkspaceUpdateRequest,
    workspace: Workspace = Depends(require_workspace_owner),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """FR-RW-04 (visibility) via general update; owner-only."""
    return await workspace_service.update_workspace(db, workspace, user, payload)


@router.delete("/{workspace_id}", status_code=204)
async def archive_workspace(
    workspace: Workspace = Depends(require_workspace_owner),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """FR-RW-05: archive (soft-delete) a workspace."""
    await workspace_service.archive_workspace(db, workspace, user)
    return None


@router.get("/{workspace_id}/activity", response_model=Page[ActivityLogOut])
async def get_activity(
    params: PageParams = Depends(),
    workspace: Workspace = Depends(require_workspace_member),
    db: AsyncSession = Depends(get_db),
):
    """FR-RW-06: chronological activity log."""
    rows, total = await workspace_service.list_activity(db, workspace, params.offset, params.page_size)
    return Page(results=rows, page=params.page, page_size=params.page_size, total_results=total)

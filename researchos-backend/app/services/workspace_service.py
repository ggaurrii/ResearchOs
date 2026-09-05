"""
Workspace service — implements FR-RW-01..07 from the SRS.
"""
import uuid
from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.models.workspace import ActivityLog, Workspace, WorkspaceMember
from app.schemas.workspace import WorkspaceCreateRequest, WorkspaceUpdateRequest


async def log_activity(
    db: AsyncSession, *, workspace_id: uuid.UUID, actor_id: uuid.UUID, event_type: str, event_data: Optional[dict] = None
) -> None:
    db.add(
        ActivityLog(
            id=uuid.uuid4(),
            workspace_id=workspace_id,
            actor_id=actor_id,
            event_type=event_type,
            event_data=event_data,
        )
    )


async def create_workspace(db: AsyncSession, owner: User, payload: WorkspaceCreateRequest) -> Workspace:
    workspace = Workspace(
        id=uuid.uuid4(),
        owner_id=owner.id,
        title=payload.title,
        domain=payload.domain,
        description=payload.description,
        visibility=payload.visibility,
        status="active",
    )
    db.add(workspace)
    await db.flush()  # populate workspace.id before referencing it below

    db.add(
        WorkspaceMember(
            id=uuid.uuid4(),
            workspace_id=workspace.id,
            user_id=owner.id,
            role_in_project="Owner",
            permission_level="owner",
        )
    )
    await log_activity(
        db, workspace_id=workspace.id, actor_id=owner.id, event_type="workspace_created",
        event_data={"title": workspace.title},
    )

    await db.commit()
    await db.refresh(workspace)
    return workspace


async def list_my_workspaces(db: AsyncSession, user: User, offset: int, limit: int) -> tuple[list[Workspace], int]:
    member_workspace_ids = select(WorkspaceMember.workspace_id).where(WorkspaceMember.user_id == user.id)

    base_query = select(Workspace).where(
        Workspace.id.in_(member_workspace_ids), Workspace.status != "deleted"
    )
    count_query = select(func.count()).select_from(
        select(Workspace.id).where(Workspace.id.in_(member_workspace_ids), Workspace.status != "deleted").subquery()
    )

    total = (await db.execute(count_query)).scalar_one()
    rows = (
        await db.execute(base_query.order_by(Workspace.created_at.desc()).offset(offset).limit(limit))
    ).scalars().all()
    return list(rows), total


async def update_workspace(db: AsyncSession, workspace: Workspace, actor: User, payload: WorkspaceUpdateRequest) -> Workspace:
    changed = {}
    for field in ("title", "domain", "description", "visibility"):
        value = getattr(payload, field)
        if value is not None:
            setattr(workspace, field, value)
            changed[field] = value

    if changed:
        await log_activity(
            db, workspace_id=workspace.id, actor_id=actor.id, event_type="workspace_updated", event_data=changed
        )
    await db.commit()
    await db.refresh(workspace)
    return workspace


async def archive_workspace(db: AsyncSession, workspace: Workspace, actor: User) -> None:
    workspace.status = "archived"
    await log_activity(db, workspace_id=workspace.id, actor_id=actor.id, event_type="workspace_archived")
    await db.commit()


async def list_activity(db: AsyncSession, workspace: Workspace, offset: int, limit: int) -> tuple[list[ActivityLog], int]:
    count_query = select(func.count()).select_from(
        select(ActivityLog.id).where(ActivityLog.workspace_id == workspace.id).subquery()
    )
    total = (await db.execute(count_query)).scalar_one()
    rows = (
        await db.execute(
            select(ActivityLog)
            .where(ActivityLog.workspace_id == workspace.id)
            .order_by(ActivityLog.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
    ).scalars().all()
    return list(rows), total

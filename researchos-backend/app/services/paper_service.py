"""
Paper persistence service — implements FR-LD-01..08 (excluding external
search, which lives in literature_service.py).
"""
import uuid
from typing import Optional

from fastapi import UploadFile
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ValidationAPIError
from app.models.paper import Paper
from app.models.user import User
from app.models.workspace import Workspace
from app.schemas.paper import PaperAddRequest
from app.services.storage_service import get_storage
from app.services.workspace_service import log_activity

MAX_UPLOAD_BYTES = 25 * 1024 * 1024  # 25 MB


async def add_paper(db: AsyncSession, workspace: Workspace, actor: User, payload: PaperAddRequest) -> Paper:
    paper = Paper(
        id=uuid.uuid4(),
        workspace_id=workspace.id,
        title=payload.title,
        authors=payload.authors or None,
        doi=payload.doi,
        source=payload.source,
        publication_year=payload.publication_year,
        abstract=payload.abstract,
        analysis_status="pending",
        added_by=actor.id,
    )
    db.add(paper)
    await log_activity(
        db, workspace_id=workspace.id, actor_id=actor.id, event_type="paper_added",
        event_data={"title": paper.title, "source": paper.source},
    )
    await db.commit()
    await db.refresh(paper)
    return paper


async def upload_paper(db: AsyncSession, workspace: Workspace, actor: User, file: UploadFile) -> Paper:
    if file.content_type not in ("application/pdf",):
        raise ValidationAPIError("Only PDF uploads are supported.", details={"field": "file"})

    content = await file.read()
    if len(content) > MAX_UPLOAD_BYTES:
        raise ValidationAPIError("Uploaded file exceeds the 25 MB limit.", details={"field": "file"})

    storage_path = await get_storage().save_paper_pdf(workspace.id, file.filename or "upload.pdf", content)

    paper = Paper(
        id=uuid.uuid4(),
        workspace_id=workspace.id,
        title=file.filename or "Untitled upload",
        source="upload",
        storage_path=storage_path,
        analysis_status="pending",
        added_by=actor.id,
    )
    db.add(paper)
    await log_activity(
        db, workspace_id=workspace.id, actor_id=actor.id, event_type="paper_uploaded",
        event_data={"filename": file.filename},
    )
    await db.commit()
    await db.refresh(paper)
    return paper


async def list_papers(
    db: AsyncSession, workspace: Workspace, offset: int, limit: int, source: Optional[str] = None
) -> tuple[list[Paper], int]:
    query = select(Paper).where(Paper.workspace_id == workspace.id)
    count_query = select(func.count()).select_from(query.subquery())

    if source:
        query = query.where(Paper.source == source)
        count_query = select(func.count()).select_from(query.subquery())

    total = (await db.execute(count_query)).scalar_one()
    rows = (
        await db.execute(query.order_by(Paper.created_at.desc()).offset(offset).limit(limit))
    ).scalars().all()
    return list(rows), total


async def get_paper_in_workspace(db: AsyncSession, workspace: Workspace, paper_id: uuid.UUID) -> Optional[Paper]:
    result = await db.execute(
        select(Paper).where(Paper.id == paper_id, Paper.workspace_id == workspace.id)
    )
    return result.scalar_one_or_none()

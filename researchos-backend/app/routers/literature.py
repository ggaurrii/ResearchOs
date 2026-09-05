import uuid

from fastapi import APIRouter, Depends, File, UploadFile

from app.core.exceptions import NotFoundError
from app.core.pagination import Page, PageParams
from app.core.rate_limit import search_rate_limit
from app.database import get_db
from app.dependencies import get_current_user, require_workspace_member
from app.models.user import User
from app.models.workspace import Workspace
from app.schemas.paper import LiteratureSearchRequest, LiteratureSearchResponse, PaperAddRequest, PaperOut
from app.services import literature_service, paper_service
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(tags=["Literature Discovery"])


@router.post(
    "/workspaces/{workspace_id}/literature/search",
    response_model=LiteratureSearchResponse,
    dependencies=[Depends(search_rate_limit)],
)
async def search_literature(
    payload: LiteratureSearchRequest,
    workspace: Workspace = Depends(require_workspace_member),
):
    """FR-LD-01/02/03/06/07: fan out to external sources, de-dupe, return
    transient results (not yet persisted to the workspace)."""
    return await literature_service.search_literature(payload)


@router.post("/workspaces/{workspace_id}/papers", response_model=PaperOut, status_code=201)
async def add_paper(
    payload: PaperAddRequest,
    workspace: Workspace = Depends(require_workspace_member),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """FR-LD-04: add a discovered paper to the workspace."""
    return await paper_service.add_paper(db, workspace, user, payload)


@router.post("/workspaces/{workspace_id}/papers/upload", response_model=PaperOut, status_code=201)
async def upload_paper(
    file: UploadFile = File(...),
    workspace: Workspace = Depends(require_workspace_member),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """FR-LD-05: upload a PDF the user already has legal access to."""
    return await paper_service.upload_paper(db, workspace, user, file)


@router.get("/workspaces/{workspace_id}/papers", response_model=Page[PaperOut])
async def list_papers(
    params: PageParams = Depends(),
    source: str | None = None,
    workspace: Workspace = Depends(require_workspace_member),
    db: AsyncSession = Depends(get_db),
):
    """FR-LD-08: list papers in the workspace, optionally filtered by source."""
    rows, total = await paper_service.list_papers(db, workspace, params.offset, params.page_size, source)
    return Page(results=rows, page=params.page, page_size=params.page_size, total_results=total)


@router.get("/workspaces/{workspace_id}/papers/{paper_id}", response_model=PaperOut)
async def get_paper(
    paper_id: uuid.UUID,
    workspace: Workspace = Depends(require_workspace_member),
    db: AsyncSession = Depends(get_db),
):
    paper = await paper_service.get_paper_in_workspace(db, workspace, paper_id)
    if paper is None:
        raise NotFoundError("Paper not found in this workspace.")
    return paper

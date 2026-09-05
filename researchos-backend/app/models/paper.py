"""
Paper model — matches the Database Design Document, Section 3.3 (papers).

analysis_status is retained for forward compatibility with Module 4 (AI
Literature Analysis), which is out of scope for this build pass; it is
always 'pending' here since no analysis pipeline runs yet.
"""
import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import CheckConstraint, ForeignKey, SmallInteger, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import ARRAY, TIMESTAMP, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.database import Base


class Paper(Base):
    __tablename__ = "papers"
    __table_args__ = (
        CheckConstraint(
            "source IN ('openalex','arxiv','semantic_scholar','pubmed','crossref','upload')",
            name="ck_paper_source",
        ),
        CheckConstraint(
            "analysis_status IN ('pending','processing','completed','failed','partial')",
            name="ck_paper_analysis_status",
        ),
        UniqueConstraint("workspace_id", "doi", name="uq_paper_workspace_doi"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workspace_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    authors: Mapped[Optional[list[str]]] = mapped_column(ARRAY(String), nullable=True)
    doi: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    source: Mapped[str] = mapped_column(String(50), nullable=False)
    publication_year: Mapped[Optional[int]] = mapped_column(SmallInteger, nullable=True)
    storage_path: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    abstract: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    analysis_status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")
    added_by: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now(), index=True
    )

    workspace: Mapped["Workspace"] = relationship(back_populates="papers")

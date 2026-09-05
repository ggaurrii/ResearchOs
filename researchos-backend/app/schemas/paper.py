import uuid
from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

Source = Literal["openalex", "arxiv", "semantic_scholar", "pubmed", "crossref", "upload"]


class SearchFilters(BaseModel):
    year_from: Optional[int] = None
    year_to: Optional[int] = None


class LiteratureSearchRequest(BaseModel):
    keywords: list[str] = Field(min_length=1)
    domain: Optional[str] = None
    filters: Optional[SearchFilters] = None


class LiteratureSearchResult(BaseModel):
    title: str
    authors: list[str] = []
    year: Optional[int] = None
    venue: Optional[str] = None
    doi: Optional[str] = None
    source: Source
    abstract_snippet: Optional[str] = None


class LiteratureSearchResponse(BaseModel):
    results: list[LiteratureSearchResult]
    sources_queried: list[str]
    sources_failed: list[str]
    total_results: int


class PaperAddRequest(BaseModel):
    title: str = Field(min_length=1, max_length=500)
    authors: list[str] = []
    doi: Optional[str] = Field(default=None, max_length=120)
    source: Source
    publication_year: Optional[int] = None
    abstract: Optional[str] = None


class PaperOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    workspace_id: uuid.UUID
    title: str
    authors: Optional[list[str]] = None
    doi: Optional[str] = None
    source: Source
    publication_year: Optional[int] = None
    storage_path: Optional[str] = None
    abstract: Optional[str] = None
    analysis_status: str
    added_by: uuid.UUID
    created_at: datetime

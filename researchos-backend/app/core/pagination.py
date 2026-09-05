"""
Pagination conventions shared across list endpoints, matching the API
Design Document, Section 2.3.
"""
from typing import Generic, Sequence, TypeVar

from fastapi import Query
from pydantic import BaseModel

T = TypeVar("T")


class PageParams:
    def __init__(
        self,
        page: int = Query(1, ge=1, description="Page number (1-indexed)."),
        page_size: int = Query(20, ge=1, le=50, description="Results per page (max 50)."),
    ):
        self.page = page
        self.page_size = page_size

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.page_size


class Page(BaseModel, Generic[T]):
    results: Sequence[T]
    page: int
    page_size: int
    total_results: int

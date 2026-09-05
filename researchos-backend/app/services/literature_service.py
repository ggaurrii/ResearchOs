"""
Literature Discovery orchestration — fans a search out to every external
source concurrently, tolerates individual source failures, and de-duplicates
results by DOI first, then by a normalized title, per the SDD's
DeduplicationEngine component (Section 4, Module 3).
"""
import asyncio
import logging
import re
from typing import Any

import httpx

from app.config import get_settings
from app.core.exceptions import UpstreamSourceError
from app.schemas.paper import LiteratureSearchRequest, LiteratureSearchResponse, LiteratureSearchResult
from app.services.literature_sources import SOURCE_FETCHERS

settings = get_settings()
logger = logging.getLogger(__name__)


def _normalize_title(title: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", title.lower())


def _dedupe(results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen_dois: set[str] = set()
    seen_titles: set[str] = set()
    deduped: list[dict[str, Any]] = []

    for r in results:
        doi = (r.get("doi") or "").lower().strip()
        norm_title = _normalize_title(r.get("title") or "")

        if doi:
            if doi in seen_dois:
                continue
            seen_dois.add(doi)
        elif norm_title in seen_titles:
            continue

        if norm_title:
            seen_titles.add(norm_title)
        deduped.append(r)

    return deduped


async def search_literature(payload: LiteratureSearchRequest, limit_per_source: int = 10) -> LiteratureSearchResponse:
    year_from = payload.filters.year_from if payload.filters else None
    year_to = payload.filters.year_to if payload.filters else None

    sources_queried = list(SOURCE_FETCHERS.keys())
    sources_failed: list[str] = []
    all_results: list[dict[str, Any]] = []

    async with httpx.AsyncClient(timeout=settings.literature_source_timeout_seconds) as client:
        tasks = {
            name: asyncio.create_task(
                fetcher(client, payload.keywords, payload.domain, year_from, year_to, limit_per_source)
            )
            for name, fetcher in SOURCE_FETCHERS.items()
        }
        for name, task in tasks.items():
            try:
                all_results.extend(await task)
            except Exception as exc:  # noqa: BLE001 — a single bad source must not break the search
                sources_failed.append(name)
                logger.warning("Literature source '%s' failed: %s", name, exc)

    if len(sources_failed) == len(sources_queried):
        raise UpstreamSourceError(
            "All external literature sources failed to respond.",
            details={"sources_failed": sources_failed},
        )

    deduped = _dedupe(all_results)
    results = [LiteratureSearchResult(**r) for r in deduped]

    return LiteratureSearchResponse(
        results=results,
        sources_queried=sources_queried,
        sources_failed=sources_failed,
        total_results=len(results),
    )

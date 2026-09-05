"""
Literature Discovery module — external source fetchers (FR-LD-01..08).

Each fetch_* function takes normalized search parameters and returns a list
of plain dicts shaped like schemas.paper.LiteratureSearchResult. Every
fetcher isolates its own failures: a broken or slow source returns an empty
list rather than raising, so literature_service can still return partial
results from the sources that succeeded (matching UPSTREAM_SOURCE_ERROR
semantics in the API Design Document — that error is only raised if *every*
source fails).

NOTE ON SANDBOX TESTING: these fetchers call public literature APIs
(api.openalex.org, export.arxiv.org, api.semanticscholar.org,
api.crossref.org, eutils.ncbi.nlm.nih.gov). The development sandbox used to
build this backend has an egress allowlist that does not include those
hosts, so live calls could not be exercised end-to-end here. Parsing logic
is unit-tested against realistic fixture payloads in
tests/test_literature_sources.py instead. Verify connectivity to each host
is permitted in your deployment environment.
"""
import logging
import xml.etree.ElementTree as ET
from typing import Any, Optional

import httpx

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


def _query_string(keywords: list[str], domain: Optional[str]) -> str:
    terms = list(keywords)
    if domain:
        terms.append(domain)
    return " ".join(terms)


async def fetch_openalex(
    client: httpx.AsyncClient, keywords: list[str], domain: Optional[str],
    year_from: Optional[int], year_to: Optional[int], limit: int = 10,
) -> list[dict[str, Any]]:
    params = {"search": _query_string(keywords, domain), "per_page": limit}
    if year_from or year_to:
        lo, hi = year_from or 1900, year_to or 2100
        params["filter"] = f"publication_year:{lo}-{hi}"

    resp = await client.get(f"{settings.openalex_base_url}/works", params=params)
    resp.raise_for_status()
    data = resp.json()

    results = []
    for item in data.get("results", []):
        authors = [
            a.get("author", {}).get("display_name")
            for a in item.get("authorships", [])
            if a.get("author", {}).get("display_name")
        ]
        venue = (item.get("primary_location") or {}).get("source") or {}
        results.append({
            "title": item.get("title") or item.get("display_name") or "Untitled",
            "authors": authors,
            "year": item.get("publication_year"),
            "venue": venue.get("display_name"),
            "doi": (item.get("doi") or "").replace("https://doi.org/", "") or None,
            "source": "openalex",
            "abstract_snippet": None,  # OpenAlex returns an inverted index; reconstruction omitted for brevity
        })
    return results


async def fetch_crossref(
    client: httpx.AsyncClient, keywords: list[str], domain: Optional[str],
    year_from: Optional[int], year_to: Optional[int], limit: int = 10,
) -> list[dict[str, Any]]:
    params = {"query": _query_string(keywords, domain), "rows": limit}

    resp = await client.get(f"{settings.crossref_base_url}/works", params=params)
    resp.raise_for_status()
    data = resp.json()

    results = []
    for item in data.get("message", {}).get("items", []):
        title_list = item.get("title") or []
        authors = [
            " ".join(filter(None, [a.get("given"), a.get("family")]))
            for a in item.get("author", [])
        ] if item.get("author") else []
        date_parts = (
            (item.get("published-print") or item.get("published-online") or {}).get("date-parts", [[None]])
        )
        year = date_parts[0][0] if date_parts and date_parts[0] else None
        if year_from and year and year < year_from:
            continue
        if year_to and year and year > year_to:
            continue
        results.append({
            "title": title_list[0] if title_list else "Untitled",
            "authors": authors,
            "year": year,
            "venue": (item.get("container-title") or [None])[0],
            "doi": item.get("DOI"),
            "source": "crossref",
            "abstract_snippet": None,
        })
    return results


async def fetch_arxiv(
    client: httpx.AsyncClient, keywords: list[str], domain: Optional[str],
    year_from: Optional[int], year_to: Optional[int], limit: int = 10,
) -> list[dict[str, Any]]:
    search_query = "all:" + "+AND+all:".join(k.replace(" ", "+") for k in keywords)
    params = {"search_query": search_query, "max_results": limit}

    resp = await client.get(settings.arxiv_base_url, params=params)
    resp.raise_for_status()

    ns = {"atom": "http://www.w3.org/2005/Atom"}
    root = ET.fromstring(resp.text)

    results = []
    for entry in root.findall("atom:entry", ns):
        title = (entry.findtext("atom:title", default="", namespaces=ns) or "").strip()
        summary = (entry.findtext("atom:summary", default="", namespaces=ns) or "").strip()
        published = entry.findtext("atom:published", default="", namespaces=ns) or ""
        year = int(published[:4]) if published[:4].isdigit() else None
        if year_from and year and year < year_from:
            continue
        if year_to and year and year > year_to:
            continue
        authors = [
            (a.findtext("atom:name", default="", namespaces=ns) or "").strip()
            for a in entry.findall("atom:author", ns)
        ]
        results.append({
            "title": title,
            "authors": authors,
            "year": year,
            "venue": "arXiv",
            "doi": None,
            "source": "arxiv",
            "abstract_snippet": (summary[:280] + "…") if len(summary) > 280 else summary,
        })
    return results


async def fetch_semantic_scholar(
    client: httpx.AsyncClient, keywords: list[str], domain: Optional[str],
    year_from: Optional[int], year_to: Optional[int], limit: int = 10,
) -> list[dict[str, Any]]:
    params = {
        "query": _query_string(keywords, domain),
        "limit": limit,
        "fields": "title,authors,year,venue,externalIds,abstract",
    }
    if year_from or year_to:
        params["year"] = f"{year_from or ''}-{year_to or ''}"

    resp = await client.get(f"{settings.semantic_scholar_base_url}/paper/search", params=params)
    resp.raise_for_status()
    data = resp.json()

    results = []
    for item in data.get("data", []):
        abstract = item.get("abstract") or ""
        results.append({
            "title": item.get("title") or "Untitled",
            "authors": [a.get("name") for a in (item.get("authors") or []) if a.get("name")],
            "year": item.get("year"),
            "venue": item.get("venue"),
            "doi": (item.get("externalIds") or {}).get("DOI"),
            "source": "semantic_scholar",
            "abstract_snippet": (abstract[:280] + "…") if len(abstract) > 280 else abstract or None,
        })
    return results


async def fetch_pubmed(
    client: httpx.AsyncClient, keywords: list[str], domain: Optional[str],
    year_from: Optional[int], year_to: Optional[int], limit: int = 10,
) -> list[dict[str, Any]]:
    search_params = {
        "db": "pubmed",
        "term": _query_string(keywords, domain),
        "retmode": "json",
        "retmax": limit,
    }
    search_resp = await client.get(f"{settings.pubmed_base_url}/esearch.fcgi", params=search_params)
    search_resp.raise_for_status()
    id_list = search_resp.json().get("esearchresult", {}).get("idlist", [])
    if not id_list:
        return []

    summary_resp = await client.get(
        f"{settings.pubmed_base_url}/esummary.fcgi",
        params={"db": "pubmed", "id": ",".join(id_list), "retmode": "json"},
    )
    summary_resp.raise_for_status()
    summary_data = summary_resp.json().get("result", {})

    results = []
    for pmid in id_list:
        item = summary_data.get(pmid)
        if not item:
            continue
        pub_date = item.get("pubdate", "")
        year = int(pub_date[:4]) if pub_date[:4].isdigit() else None
        doi = next(
            (aid.get("value") for aid in item.get("articleids", []) if aid.get("idtype") == "doi"), None
        )
        results.append({
            "title": item.get("title") or "Untitled",
            "authors": [a.get("name") for a in item.get("authors", []) if a.get("name")],
            "year": year,
            "venue": item.get("fulljournalname") or item.get("source"),
            "doi": doi,
            "source": "pubmed",
            "abstract_snippet": None,
        })
    return results


SOURCE_FETCHERS = {
    "openalex": fetch_openalex,
    "crossref": fetch_crossref,
    "arxiv": fetch_arxiv,
    "semantic_scholar": fetch_semantic_scholar,
    "pubmed": fetch_pubmed,
}

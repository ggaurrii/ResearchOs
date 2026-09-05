"""
Application configuration.

Settings are loaded from environment variables (and a local .env file in
development). See .env.example for the full list of supported variables.
"""
from functools import lru_cache
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # --- General ---
    app_name: str = "ResearchOS API"
    api_v1_prefix: str = "/api/v1"
    environment: str = "development"
    debug: bool = True

    # --- Database ---
    database_url: str = "postgresql+asyncpg://researchos:researchos_dev@localhost:5432/researchos"

    # --- Redis ---
    redis_url: str = "redis://localhost:6379/0"

    # --- Auth / JWT ---
    jwt_secret_key: str = "CHANGE_ME_IN_PRODUCTION"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 30

    # --- CORS ---
    cors_allow_origins: List[str] = ["http://localhost:3000"]

    # --- Rate limiting ---
    default_rate_limit_per_minute: int = 300
    search_rate_limit_per_minute: int = 20

    # --- File storage ---
    # Local disk storage is used in this development build; the SDD specifies
    # MinIO/S3 for production. Swap StorageBackend implementations in
    # app/services/storage_service.py to migrate without touching callers.
    storage_root: str = "./storage"

    # --- External literature APIs ---
    openalex_base_url: str = "https://api.openalex.org"
    arxiv_base_url: str = "http://export.arxiv.org/api/query"
    semantic_scholar_base_url: str = "https://api.semanticscholar.org/graph/v1"
    crossref_base_url: str = "https://api.crossref.org"
    pubmed_base_url: str = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
    literature_source_timeout_seconds: float = 8.0

    # --- Account lockout (FR-UM-10) ---
    max_failed_login_attempts: int = 5


@lru_cache
def get_settings() -> Settings:
    return Settings()

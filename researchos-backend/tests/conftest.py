import uuid

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.config import get_settings
from app.database import Base, get_db
from app.main import app
from app.redis_client import get_redis

TEST_DATABASE_URL = "postgresql+asyncpg://researchos:researchos_dev@localhost:5432/researchos_test"

# NullPool avoids reusing a pooled asyncpg connection across the different
# event loops that pytest-asyncio creates between test functions; each
# checkout opens a fresh connection instead.
test_engine = create_async_engine(TEST_DATABASE_URL, future=True, poolclass=NullPool)
TestSessionLocal = async_sessionmaker(bind=test_engine, class_=AsyncSession, expire_on_commit=False)


async def _override_get_redis():
    """A brand-new Redis connection per call, rather than the app's shared,
    process-lifetime connection pool — avoids handing an asyncio-loop-bound
    socket between the different event loops pytest-asyncio uses per test."""
    settings = get_settings()
    client = Redis.from_url(settings.redis_url, decode_responses=True)
    try:
        yield client
    finally:
        await client.aclose()


app.dependency_overrides[get_redis] = _override_get_redis


@pytest_asyncio.fixture(scope="session", autouse=True)
async def _create_schema():
    """Create all tables once for the test session and drop them afterward,
    so tests run against a real Postgres schema (matching production) rather
    than SQLite, which cannot represent ARRAY/JSONB columns used here."""
    from app.redis_client import get_redis

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    redis = get_redis()
    await redis.flushdb()
    await redis.aclose()

    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture(autouse=True)
async def _clean_tables():
    """Truncate all tables between tests so each test starts from a clean slate."""
    yield
    async with test_engine.begin() as conn:
        for table in reversed(Base.metadata.sorted_tables):
            await conn.execute(table.delete())


async def _override_get_db():
    async with TestSessionLocal() as session:
        yield session


app.dependency_overrides[get_db] = _override_get_db


@pytest_asyncio.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
        yield ac


def unique_email(prefix: str = "user") -> str:
    return f"{prefix}_{uuid.uuid4().hex[:8]}@example.edu"

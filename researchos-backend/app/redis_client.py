"""
Redis connection used for caching, rate limiting, and (in future work)
as the Celery broker and Socket.IO pub/sub backplane per the SDD, Section 5.5.
"""
from functools import lru_cache

from redis.asyncio import ConnectionPool, Redis

from app.config import get_settings

settings = get_settings()


@lru_cache
def get_redis_pool() -> ConnectionPool:
    return ConnectionPool.from_url(settings.redis_url, decode_responses=True)


def get_redis() -> Redis:
    """FastAPI dependency returning a Redis client bound to the shared pool."""
    return Redis(connection_pool=get_redis_pool())

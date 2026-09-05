"""
Simple fixed-window rate limiter backed by Redis, matching the API Design
Document, Section 2.7. Not exact leaky-bucket precision, but sufficient to
protect expensive endpoints (literature search, AI-assist) from abuse.
"""
import time

from fastapi import Depends, Request
from redis.asyncio import Redis

from app.core.exceptions import RateLimitedError
from app.redis_client import get_redis


class RateLimiter:
    def __init__(self, *, limit_per_minute: int, bucket: str):
        self.limit_per_minute = limit_per_minute
        self.bucket = bucket

    async def __call__(self, request: Request, redis: Redis = Depends(get_redis)) -> None:
        identity = request.headers.get("Authorization", request.client.host if request.client else "anon")
        window = int(time.time() // 60)
        key = f"ratelimit:{self.bucket}:{identity}:{window}"

        count = await redis.incr(key)
        if count == 1:
            await redis.expire(key, 60)

        if count > self.limit_per_minute:
            raise RateLimitedError(
                f"Rate limit of {self.limit_per_minute} requests/minute exceeded for this endpoint.",
                details={"retry_after_seconds": 60 - int(time.time() % 60)},
            )


default_rate_limit = RateLimiter(limit_per_minute=300, bucket="default")
search_rate_limit = RateLimiter(limit_per_minute=20, bucket="search")

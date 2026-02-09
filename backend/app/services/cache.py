"""
Cache Service
─────────────
Redis-backed caching layer for search results and deal data.
Falls back to an in-memory LRU dict when Redis is not available.
"""

from __future__ import annotations

import json
import hashlib
from datetime import timedelta
from typing import Any, Optional

import structlog

logger = structlog.get_logger()

# In-memory fallback (limited size)
_MEM_CACHE: dict[str, tuple[float, str]] = {}
_MAX_MEM = 1000


def _cache_key(prefix: str, params: dict[str, Any]) -> str:
    raw = json.dumps(params, sort_keys=True, default=str)
    h = hashlib.sha256(raw.encode()).hexdigest()[:16]
    return f"sd:{prefix}:{h}"


class CacheService:
    """Async cache abstraction.  Uses Redis when available, memory otherwise."""

    def __init__(self, redis_url: str | None = None) -> None:
        self._redis = None
        self._redis_url = redis_url

    async def connect(self) -> None:
        if not self._redis_url:
            return
        try:
            import redis.asyncio as aioredis
            self._redis = aioredis.from_url(self._redis_url, decode_responses=True)
            await self._redis.ping()
            logger.info("cache.redis.connected")
        except Exception as exc:
            logger.warning("cache.redis.unavailable", error=str(exc))
            self._redis = None

    async def get(self, prefix: str, params: dict[str, Any]) -> Optional[Any]:
        key = _cache_key(prefix, params)
        if self._redis:
            raw = await self._redis.get(key)
            if raw:
                return json.loads(raw)
        elif key in _MEM_CACHE:
            _, raw = _MEM_CACHE[key]
            return json.loads(raw)
        return None

    async def set(
        self,
        prefix: str,
        params: dict[str, Any],
        value: Any,
        ttl: int = 300,
    ) -> None:
        key = _cache_key(prefix, params)
        raw = json.dumps(value, default=str)
        if self._redis:
            await self._redis.setex(key, timedelta(seconds=ttl), raw)
        else:
            if len(_MEM_CACHE) >= _MAX_MEM:
                oldest = next(iter(_MEM_CACHE))
                del _MEM_CACHE[oldest]
            import time
            _MEM_CACHE[key] = (time.time() + ttl, raw)

    async def invalidate(self, prefix: str, params: dict[str, Any]) -> None:
        key = _cache_key(prefix, params)
        if self._redis:
            await self._redis.delete(key)
        elif key in _MEM_CACHE:
            del _MEM_CACHE[key]


# Singleton
cache = CacheService()

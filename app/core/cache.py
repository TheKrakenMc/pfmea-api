"""Distributed cache service backed by Redis.

Provides:
* ``CacheService`` — low-level get/set/invalidate against a Redis instance.
* ``cached`` — decorator for transparently caching endpoint responses.
* ``get_cache_service`` — singleton accessor (lazy-initialised).

When ``REDIS_URL`` is **not** configured the service degrades gracefully
to a no-op (all cache misses, no errors).
"""

from __future__ import annotations

import json
import logging
from functools import wraps
from typing import Any, Callable, Optional

logger = logging.getLogger("pfmea.cache")

# Global singleton; set by ``init_cache``.
_cache_service: Optional["CacheService"] = None


class CacheService:
    """Thin async wrapper over Redis with JSON serialisation."""

    DEFAULT_TTL = 300  # 5 minutes

    def __init__(self, redis_url: str):
        import redis.asyncio as redis_lib

        self.redis = redis_lib.from_url(redis_url, decode_responses=True)

    async def get(self, key: str) -> Optional[Any]:
        """Return the cached value or ``None`` on miss."""
        data = await self.redis.get(key)
        if data is None:
            return None
        try:
            return json.loads(data)
        except (json.JSONDecodeError, TypeError):
            return None

    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Store *value* under *key* with the given TTL (seconds)."""
        await self.redis.setex(
            key,
            ttl or self.DEFAULT_TTL,
            json.dumps(value, default=str),
        )

    async def invalidate(self, pattern: str) -> int:
        """Delete all keys matching *pattern* (e.g. ``products:*``).

        Returns the number of keys deleted.
        """
        keys = await self.redis.keys(pattern)
        if keys:
            return await self.redis.delete(*keys)
        return 0

    async def close(self) -> None:
        """Shutdown the connection pool."""
        await self.redis.close()


# ---------------------------------------------------------------------------
# Public helpers
# ---------------------------------------------------------------------------


def init_cache(redis_url: Optional[str]) -> Optional[CacheService]:
    """Create (or skip) the global ``CacheService``.

    Call once at application startup.
    """
    global _cache_service
    if not redis_url:
        logger.warning("REDIS_URL not set — cache disabled (no-op mode)")
        return None
    _cache_service = CacheService(redis_url)
    logger.info("Cache initialised (Redis: %s)", redis_url.split("@")[-1])
    return _cache_service


def get_cache_service() -> Optional[CacheService]:
    """Return the global cache instance or ``None``."""
    return _cache_service


def cached(key_pattern: str, ttl: int = 300) -> Callable:
    """Decorator for caching endpoint return values.

    ``key_pattern`` may contain ``{name}`` placeholders that are
    filled from the decorated function's **kwargs**.

    Example::

        @cached("products:{plant_id}", ttl=600)
        async def list_products(plant_id: int, ...):
            ...

    If Redis is unavailable the decorator is a transparent pass-through.
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            cache = get_cache_service()
            if cache is None:
                return await func(*args, **kwargs)

            cache_key = key_pattern.format(**kwargs)

            cached_data = await cache.get(cache_key)
            if cached_data is not None:
                return cached_data

            result = await func(*args, **kwargs)
            await cache.set(cache_key, result, ttl)
            return result

        return wrapper

    return decorator

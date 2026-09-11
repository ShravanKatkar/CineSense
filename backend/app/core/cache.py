"""
CineSense Multi-Tier Cache Layer
Supports Redis (asyncio) with automatic fallback to high-speed in-memory TTL caching.
"""

from __future__ import annotations

import asyncio
import functools
import json
import logging
import time
from typing import Any, Callable

from cachetools import TTLCache

from app.core.config import get_settings

log = logging.getLogger(__name__)


class CacheService:
    def __init__(self, default_ttl: int = 3600, max_memory_items: int = 10000):
        self.default_ttl = default_ttl
        self.max_memory_items = max_memory_items
        self._redis = None
        self._use_redis = False
        self._memory_cache = TTLCache(maxsize=max_memory_items, ttl=default_ttl)
        self._hits = 0
        self._misses = 0
        self._sets = 0
        self._initialized = False

    async def init(self) -> None:
        """Attempt to connect to Redis if configured. Falls back gracefully to memory cache."""
        if self._initialized:
            return

        settings = get_settings()
        redis_url = getattr(settings, "redis_url", None)

        if redis_url:
            try:
                import redis.asyncio as aioredis

                client = aioredis.from_url(
                    redis_url,
                    decode_responses=True,
                    socket_connect_timeout=1.5,
                    socket_timeout=1.5,
                )
                await client.ping()
                self._redis = client
                self._use_redis = True
                log.info("cache_service: successfully connected to Redis at %s", redis_url)
            except Exception as exc:
                self._use_redis = False
                self._redis = None
                log.info(
                    "cache_service: Redis not reachable (%s). Activated in-memory TTL cache fallback.",
                    exc,
                )
        else:
            self._use_redis = False
            log.info("cache_service: No REDIS_URL configured. Using in-memory TTL cache.")

        self._initialized = True

    async def close(self) -> None:
        """Close any active Redis connections."""
        if self._redis:
            try:
                await self._redis.aclose()
            except Exception:
                pass
            self._redis = None
        self._initialized = False

    async def get(self, key: str) -> Any | None:
        """Retrieve item from cache (Redis or memory). Returns None on miss."""
        if not self._initialized:
            await self.init()

        if self._use_redis and self._redis:
            try:
                raw = await self._redis.get(key)
                if raw is not None:
                    self._hits += 1
                    try:
                        return json.loads(raw)
                    except (json.JSONDecodeError, TypeError):
                        return raw
            except Exception as exc:
                log.debug("cache_redis_get_error key=%s: %s", key, exc)

        # Fall back to memory cache
        if key in self._memory_cache:
            self._hits += 1
            return self._memory_cache[key]

        self._misses += 1
        return None

    async def set(self, key: str, value: Any, ttl_seconds: int | None = None) -> None:
        """Store item in cache with TTL."""
        if not self._initialized:
            await self.init()

        ttl = ttl_seconds if ttl_seconds is not None else self.default_ttl
        self._sets += 1

        if self._use_redis and self._redis:
            try:
                serialized = json.dumps(value) if not isinstance(value, str) else value
                await self._redis.set(key, serialized, ex=ttl)
                return
            except Exception as exc:
                log.debug("cache_redis_set_error key=%s: %s", key, exc)

        # Memory cache store
        self._memory_cache[key] = value

    async def delete(self, key: str) -> None:
        """Delete specific key from cache."""
        if self._use_redis and self._redis:
            try:
                await self._redis.delete(key)
            except Exception:
                pass

        self._memory_cache.pop(key, None)

    async def clear(self, prefix: str = "") -> None:
        """Flush keys matching prefix or all keys if prefix is empty."""
        if self._use_redis and self._redis:
            try:
                if prefix:
                    keys = await self._redis.keys(f"{prefix}*")
                    if keys:
                        await self._redis.delete(*keys)
                else:
                    await self._redis.flushdb()
            except Exception:
                pass

        if prefix:
            keys_to_del = [k for k in self._memory_cache if str(k).startswith(prefix)]
            for k in keys_to_del:
                self._memory_cache.pop(k, None)
        else:
            self._memory_cache.clear()

    def stats(self) -> dict:
        """Return cache health and telemetry metrics."""
        total_requests = self._hits + self._misses
        hit_rate = round((self._hits / total_requests) * 100, 2) if total_requests > 0 else 0.0

        return {
            "backend": "redis" if self._use_redis else "memory",
            "hits": self._hits,
            "misses": self._misses,
            "total_sets": self._sets,
            "total_requests": total_requests,
            "hit_rate_pct": hit_rate,
            "memory_items_count": len(self._memory_cache),
            "max_memory_capacity": self.max_memory_items,
        }


# Global singleton cache instance
cache_service = CacheService()


def cached(ttl_seconds: int = 3600, prefix: str = "cinesense"):
    """Decorator for caching async function results."""

    def decorator(func: Callable):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # Serialize arguments to create unique cache key
            key_parts = [prefix, func.__name__]
            for a in args:
                if hasattr(a, "__dict__"):
                    key_parts.append(str(id(a)))
                else:
                    key_parts.append(str(a))
            for k, v in sorted(kwargs.items()):
                key_parts.append(f"{k}={v}")

            cache_key = ":".join(key_parts)
            cached_val = await cache_service.get(cache_key)
            if cached_val is not None:
                return cached_val

            result = await func(*args, **kwargs)
            if result is not None:
                await cache_service.set(cache_key, result, ttl_seconds=ttl_seconds)
            return result

        return wrapper

    return decorator

from collections.abc import Callable
from functools import wraps
from typing import Any, TypeVar

from cachetools import TTLCache

F = TypeVar("F", bound=Callable[..., Any])


class InMemoryCache:
    """Thread-safe TTLCache wrapper."""
    def __init__(self, maxsize: int = 1000, ttl: float = 300.0):
        self._cache: TTLCache[str, Any] = TTLCache(maxsize=maxsize, ttl=ttl)

    def get(self, key: str) -> Any | None:
        return self._cache.get(key)

    def set(self, key: str, value: Any) -> None:
        self._cache[key] = value

    def invalidate(self, key: str) -> None:
        self._cache.pop(key, None)

    def clear(self) -> None:
        self._cache.clear()


# Default endpoint cache (5 minutes TTL)
default_cache = InMemoryCache(maxsize=500, ttl=300.0)


def cached_endpoint(ttl: float = 300.0, maxsize: int = 500) -> Callable[[F], F]:
    """Decorator to cache endpoint or service function results in memory."""
    cache = InMemoryCache(maxsize=maxsize, ttl=ttl)

    def decorator(func: F) -> F:
        @wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            key = f"{func.__module__}:{func.__qualname__}:{args}:{sorted(kwargs.items())}"
            cached_val = cache.get(key)
            if cached_val is not None:
                return cached_val
            result = await func(*args, **kwargs)
            cache.set(key, result)
            return result

        @wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            key = f"{func.__module__}:{func.__qualname__}:{args}:{sorted(kwargs.items())}"
            cached_val = cache.get(key)
            if cached_val is not None:
                return cached_val
            result = func(*args, **kwargs)
            cache.set(key, result)
            return result

        import inspect
        return async_wrapper if inspect.iscoroutinefunction(func) else sync_wrapper  # type: ignore

    return decorator

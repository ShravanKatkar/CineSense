from unittest.mock import AsyncMock, patch
import pytest
from httpx import ASGITransport, AsyncClient

from app.core.cache import CacheService, cached
from app.main import app
from app.services.worker import BackgroundIngestionWorker


@pytest.mark.asyncio
async def test_cache_service_in_memory():
    # Instantiate standalone cache service with 5 items max
    cache = CacheService(default_ttl=60, max_memory_items=5)
    await cache.init()

    # Verify initial stats
    initial_stats = cache.stats()
    assert initial_stats["backend"] == "memory"
    assert initial_stats["hits"] == 0
    assert initial_stats["misses"] == 0

    # Test cache miss
    miss = await cache.get("nonexistent_key")
    assert miss is None
    assert cache.stats()["misses"] == 1

    # Test cache set and hit
    await cache.set("sample_key", {"title": "Inception", "year": 2010})
    hit = await cache.get("sample_key")
    assert hit is not None
    assert hit["title"] == "Inception"
    assert cache.stats()["hits"] == 1
    assert cache.stats()["hit_rate_pct"] == 50.0  # 1 hit, 1 miss

    # Test delete
    await cache.delete("sample_key")
    assert await cache.get("sample_key") is None

    # Test clear
    await cache.set("prefix:1", "item1")
    await cache.set("prefix:2", "item2")
    await cache.set("other:3", "item3")
    await cache.clear(prefix="prefix:")
    assert await cache.get("prefix:1") is None
    assert await cache.get("prefix:2") is None
    assert await cache.get("other:3") == "item3"

    await cache.clear()
    assert await cache.get("other:3") is None
    await cache.close()


@pytest.mark.asyncio
async def test_cached_decorator():
    call_counter = 0

    @cached(ttl_seconds=60, prefix="test_calc")
    async def expensive_calc(a: int, b: int) -> int:
        nonlocal call_counter
        call_counter += 1
        return a + b

    # First call: computes and stores
    res1 = await expensive_calc(10, 20)
    assert res1 == 30
    assert call_counter == 1

    # Second call with same arguments: should hit cache
    res2 = await expensive_calc(10, 20)
    assert res2 == 30
    assert call_counter == 1  # Not incremented!

    # Different arguments: computes
    res3 = await expensive_calc(10, 30)
    assert res3 == 40
    assert call_counter == 2


@pytest.mark.asyncio
async def test_background_worker_status_and_sync():
    worker = BackgroundIngestionWorker()
    status = worker.get_status()
    assert "worker_active" in status
    assert "status" in status
    assert status["total_synced_movies"] == 0

    # Mock tmdb services for sync test
    with (
        patch("app.services.tmdb.get_trending", new_callable=AsyncMock) as mock_trending,
        patch("app.services.tmdb.get_popular", new_callable=AsyncMock) as mock_pop,
        patch("app.services.tmdb.get_upcoming", new_callable=AsyncMock) as mock_upcoming,
        patch("app.services.tmdb.get_videos", new_callable=AsyncMock) as mock_videos,
        patch("app.services.tmdb.get_watch_providers", new_callable=AsyncMock) as mock_prov,
    ):
        mock_trending.return_value = [{"id": 100, "title": "Movie A"}]
        mock_pop.return_value = [{"id": 101, "title": "Movie B"}]
        mock_upcoming.return_value = []
        mock_videos.return_value = []
        mock_prov.return_value = {}

        result = await worker.sync_tmdb_feed()
        assert result["status"] == "success"
        assert result["synced_count"] == 2
        assert worker.get_status()["total_synced_movies"] == 2


@pytest.mark.asyncio
async def test_system_diagnostics_api():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # 1. System Status
        status_res = await ac.get("/api/v1/system/status")
        assert status_res.status_code == 200
        data = status_res.json()
        assert "cache" in data
        assert "worker" in data
        assert "backend" in data["cache"]

        # 2. Trigger Sync
        sync_res = await ac.post("/api/v1/system/sync")
        assert sync_res.status_code == 200
        assert sync_res.json()["status"] == "sync_dispatched"

        # 3. Cache Clear
        clear_res = await ac.post("/api/v1/system/cache/clear?prefix=test:")
        assert clear_res.status_code == 200
        assert clear_res.json()["status"] == "cleared"

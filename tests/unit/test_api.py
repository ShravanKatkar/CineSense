import pytest
from httpx import ASGITransport, AsyncClient
from app.main import app


@pytest.mark.asyncio
async def test_health_check_endpoint():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res = await ac.get("/api/v1/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "ok"


@pytest.mark.asyncio
async def test_meta_stats_endpoint():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res = await ac.get("/api/v1/meta/stats")
    assert res.status_code == 200
    data = res.json()
    assert data["n_movies"] > 9000


@pytest.mark.asyncio
async def test_list_movies_endpoint():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res = await ac.get("/api/v1/movies?page=1&page_size=10")
    assert res.status_code == 200
    data = res.json()
    assert len(data["items"]) == 10
    assert data["total"] > 9000


@pytest.mark.asyncio
async def test_movie_detail_endpoint():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res = await ac.get("/api/v1/movies/1")  # Toy Story (movielens_id = 1)
    assert res.status_code == 200
    data = res.json()
    assert "Toy Story" in data["title"]


@pytest.mark.asyncio
async def test_similar_movies_endpoint():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res = await ac.get("/api/v1/movies/1/similar?k=5")
    assert res.status_code == 200
    data = res.json()
    assert len(data) == 5


@pytest.mark.asyncio
async def test_cold_start_recommendations_endpoint():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res = await ac.get("/api/v1/recommendations/cold-start?k=10")
    assert res.status_code == 200
    data = res.json()
    assert len(data) == 10

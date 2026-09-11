import pytest
from httpx import ASGITransport, AsyncClient
from app.main import app


@pytest.mark.asyncio
async def test_compare_movies_endpoint():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res = await ac.post(
            "/api/v1/movies/compare",
            json={"movie_id_a": 1, "movie_id_b": 260},  # Toy Story vs Star Wars
        )
    assert res.status_code == 200
    data = res.json()
    assert "movie_a" in data and "movie_b" in data
    assert "metrics_a" in data and "metrics_b" in data
    assert "pacing" in data["metrics_a"]
    assert "visual_spectacle" in data["metrics_b"]
    assert len(data["tradeoffs"]) >= 2
    assert "winner_for_mood" in data
    assert "ai_verdict" in data
    assert len(data["ai_verdict"]) > 10


@pytest.mark.asyncio
async def test_watch_tonight_wizard_endpoint():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res = await ac.post(
            "/api/v1/recommendations/wizard",
            json={
                "available_time": "standard",
                "mood": "thrilling",
                "company": "solo",
                "language": "any",
            },
        )
    assert res.status_code == 200
    data = res.json()
    assert "night_vibe_summary" in data
    assert "recommendations" in data
    assert len(data["recommendations"]) <= 3
    if data["recommendations"]:
        first = data["recommendations"][0]
        assert "title" in first
        assert "reason" in first


@pytest.mark.asyncio
async def test_movie_night_group_endpoint():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res = await ac.post(
            "/api/v1/recommendations/movie-night",
            json={
                "participants": [
                    {"name": "Alex", "favorite_genres": ["Action", "Sci-Fi"]},
                    {"name": "Maya", "favorite_genres": ["Drama", "Romance"]},
                ]
            },
        )
    assert res.status_code == 200
    data = res.json()
    assert "group_compatibility_score" in data
    assert 0 <= data["group_compatibility_score"] <= 100
    assert "consensus_recommendations" in data
    assert len(data["consensus_recommendations"]) > 0
    first = data["consensus_recommendations"][0]
    assert "compromise_score" in first
    assert "appeal_per_participant" in first
    assert "Alex" in first["appeal_per_participant"]
    assert "Maya" in first["appeal_per_participant"]

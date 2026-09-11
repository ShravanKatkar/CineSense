from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock
import pytest
from httpx import ASGITransport, AsyncClient

from app.api.v1.deps import get_current_user
from app.db.session import get_db_session
from app.main import app
from app.models.users import Favorite, Rating, User


@pytest.fixture
def mock_db():
    session = AsyncMock()
    # Mock execute result
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_result.scalars.return_value.all.return_value = []
    mock_result.scalar.return_value = 0
    session.execute.return_value = mock_result
    session.commit = AsyncMock()
    session.add = MagicMock()

    async def _fake_refresh(obj):
        if getattr(obj, "id", None) is None:
            obj.id = 999
        if getattr(obj, "is_seed", None) is None:
            obj.is_seed = False
        if getattr(obj, "created_at", None) is None:
            obj.created_at = datetime.now(UTC)
        if getattr(obj, "updated_at", None) is None:
            obj.updated_at = datetime.now(UTC)

    session.refresh = AsyncMock(side_effect=_fake_refresh)

    async def _get_db():
        yield session

    app.dependency_overrides[get_db_session] = _get_db
    yield session
    app.dependency_overrides.pop(get_db_session, None)


@pytest.fixture
def mock_user():
    user = User(
        id=101,
        email="cinephile@example.com",
        username="cine_enthusiast",
        is_active=True,
        is_seed=False,
        created_at=datetime.now(UTC),
    )
    app.dependency_overrides[get_current_user] = lambda: user
    yield user
    app.dependency_overrides.pop(get_current_user, None)


@pytest.mark.asyncio
async def test_auth_registration_and_cloud_sync(mock_db, mock_user):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # 1. Register with mocked DB session
        reg_res = await ac.post(
            "/api/v1/auth/register",
            json={
                "email": "test_fan@example.com",
                "username": "test_fan",
                "password": "SuperSecurePassword123!",
            },
        )
        assert reg_res.status_code == 201
        data = reg_res.json()
        assert "access_token" in data
        assert data["user"]["email"] == "test_fan@example.com"

        # 2. Get Current Authenticated User Profile
        me_res = await ac.get("/api/v1/auth/me")
        assert me_res.status_code == 200
        assert me_res.json()["username"] == "cine_enthusiast"

        # 3. Add to Cloud Favorites
        fav_res = await ac.post("/api/v1/users/me/favorites/1")
        assert fav_res.status_code == 201
        assert fav_res.json()["status"] == "added"

        # 4. Upsert Star Rating
        rate_res = await ac.put(
            "/api/v1/users/me/ratings/1",
            json={"rating": 5.0},
        )
        assert rate_res.status_code == 200
        assert rate_res.json()["rating"] == 5.0


@pytest.mark.asyncio
async def test_tmdb_trailers_and_watch_providers():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # 1. Movie Videos (Official YouTube Trailers)
        vid_res = await ac.get("/api/v1/movies/1/videos")
        assert vid_res.status_code == 200
        vid_data = vid_res.json()
        assert "videos" in vid_data
        assert isinstance(vid_data["videos"], list)

        # 2. Movie Watch Providers (Streaming Services)
        prov_res = await ac.get("/api/v1/movies/1/watch-providers?country=US")
        assert prov_res.status_code == 200
        prov_data = prov_res.json()
        assert "flatrate" in prov_data
        assert "rent" in prov_data

        # 3. Upcoming Theatrical Releases
        up_res = await ac.get("/api/v1/movies/upcoming?page=1")
        assert up_res.status_code == 200
        up_movies = up_res.json()
        assert isinstance(up_movies, list)


@pytest.mark.asyncio
async def test_realtime_feedback_and_session_tuning():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # 1. Record Implicit Telemetry Feedback
        fb_res = await ac.post(
            "/api/v1/recommendations/feedback",
            json={
                "event_type": "trailer_watch",
                "movie_id": 1,
                "session_id": "test-session-123",
                "metadata": {"title": "Toy Story", "source": "hero_banner"},
            },
        )
        assert fb_res.status_code == 200
        fb_data = fb_res.json()
        assert fb_data["status"] == "recorded"
        assert "event_id" in fb_data

        # 2. Fetch Telemetry Metrics for Dashboard
        metrics_res = await ac.get("/api/v1/recommendations/feedback/metrics")
        assert metrics_res.status_code == 200
        metrics = metrics_res.json()
        assert metrics["total_interactions"] >= 1
        assert "event_breakdown" in metrics
        assert "trailer_watch" in metrics["event_breakdown"]

        # 3. Request Real-Time Session Tuning Recommendations
        tune_res = await ac.post(
            "/api/v1/recommendations/session-tune",
            json={"seed_ids": [1], "k": 6},
        )
        assert tune_res.status_code == 200
        tuned = tune_res.json()
        assert isinstance(tuned, list)
        if tuned:
            assert "title" in tuned[0]
            assert "score" in tuned[0]

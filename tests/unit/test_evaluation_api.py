import pytest
from httpx import ASGITransport, AsyncClient
from app.main import app


@pytest.mark.asyncio
async def test_get_benchmarks_endpoint():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res = await ac.get("/api/v1/evaluation/benchmarks")
    assert res.status_code == 200
    data = res.json()

    # Verify summary section
    assert "summary" in data
    summary = data["summary"]
    assert summary["total_test_users"] == 561
    assert summary["total_movies"] == 9741
    assert "ALS" in summary["top_accuracy_model"]
    assert "Hybrid" in summary["top_diversity_model"]

    # Verify models section
    assert "models" in data
    models = data["models"]
    assert len(models) == 6

    model_names = [m["name"] for m in models]
    assert "Popularity (weighted)" in model_names
    assert "TF-IDF content" in model_names
    assert "Embedding kNN" in model_names
    assert "Item-item CF" in model_names
    assert "ALS (64 factors)" in model_names
    assert "Hybrid RRF" in model_names

    # Check metric constraints
    for m in models:
        assert 0.0 <= m["recall_at_10"] <= 1.0
        assert 0.0 <= m["precision_at_10"] <= 1.0
        assert 0.0 <= m["ndcg_at_10"] <= 1.0
        assert 0.0 <= m["coverage_pct"] <= 100.0
        assert 0.0 <= m["diversity_score"] <= 1.0
        assert m["latency_p95_ms"] > 0.0
        assert len(m["strengths"]) > 0
        assert len(m["tradeoffs"]) > 0

    # Verify GenAI metrics section
    assert "genai" in data
    genai = data["genai"]
    assert genai["grounding_rate_pct"] == 100.0
    assert genai["hallucinated_ids_count"] == 0
    assert genai["tool_execution_success_rate"] > 95.0
    assert len(genai["tested_tools"]) == 5

    # Verify formulas section
    assert "formulas" in data
    assert len(data["formulas"]) >= 4
    for f in data["formulas"]:
        assert "name" in f and "formula" in f and "explanation" in f


@pytest.mark.asyncio
async def test_get_genai_evaluation_endpoint():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res = await ac.get("/api/v1/evaluation/genai")
    assert res.status_code == 200
    data = res.json()
    assert data["grounding_rate_pct"] == 100.0
    assert data["hallucinated_ids_count"] == 0
    assert "search_movies" in data["tested_tools"]

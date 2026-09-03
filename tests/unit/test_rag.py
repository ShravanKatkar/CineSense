import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.rag.grounding import validate_grounding
from app.rag.intent import rule_based_intent_parser


def test_rule_based_intent_parser():
    intent = rule_based_intent_parser("Show me funny action movies from the 90s under 2 hours")
    assert "Comedy" in intent.genres_include
    assert "Action" in intent.genres_include
    assert intent.year_min == 1990
    assert intent.year_max == 1999
    assert intent.runtime_max == 120


def test_grounding_validation():
    candidates = [
        {"title": "Toy Story (1995)", "director_names": ["John Lasseter"], "genre_names": ["Animation", "Comedy"]},
        {"title": "The Matrix (1999)", "director_names": ["Lana Wachowski"], "genre_names": ["Action", "Sci-Fi"]},
    ]

    valid_text = "Here is 'Toy Story (1995)' directed by John Lasseter."
    is_grounded, violations = validate_grounding(valid_text, candidates)
    assert is_grounded is True
    assert len(violations) == 0

    hallucinated_text = "Check out 'Inception' starring Leonardo DiCaprio."
    is_grounded, violations = validate_grounding(hallucinated_text, candidates)
    assert is_grounded is False
    assert len(violations) > 0


@pytest.mark.asyncio
async def test_ai_rag_search_endpoint():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res = await ac.post("/api/v1/ai/search", json={"query": "scary horror movies", "k": 5})

    assert res.status_code == 200
    data = res.json()
    assert data["query"] == "scary horror movies"
    assert len(data["items"]) == 5
    assert data["meta"]["grounding_violations"] == 0

import pytest
from app.rag.tools import TOOL_SCHEMAS, dispatch_tool_call
from app.rag.agent import run_agent
from app.rag.grounding import validate_grounding


def test_tool_schemas_specification():
    """Ensure all 5 required tools are registered with valid function calling schemas."""
    tool_names = [t["function"]["name"] for t in TOOL_SCHEMAS]
    expected_tools = [
        "search_movies",
        "get_movie_details",
        "get_similar_movies",
        "get_user_taste_profile",
        "compare_movies",
    ]
    for exp in expected_tools:
        assert exp in tool_names, f"Missing tool {exp} in TOOL_SCHEMAS"


@pytest.mark.asyncio
async def test_dispatch_search_movies_tool():
    """Verify tool_search_movies returns valid candidates."""
    res = await dispatch_tool_call("search_movies", {"query": "Inception"})
    assert "results" in res
    assert len(res["results"]) > 0
    assert any("Inception" in m["title"] for m in res["results"])


@pytest.mark.asyncio
async def test_dispatch_get_movie_details_tool():
    """Verify get_movie_details returns director and rating."""
    res = await dispatch_tool_call("get_movie_details", {"movie_id": 1})
    assert "details" in res
    assert "title" in res["details"]
    assert "rating" in res["details"]


@pytest.mark.asyncio
async def test_dispatch_compare_movies_tool():
    """Verify compare_movies generates side-by-side comparison."""
    res = await dispatch_tool_call("compare_movies", {"movie_id_a": 1, "movie_id_b": 2})
    assert "comparison" in res
    assert "movie_a" in res["comparison"]
    assert "movie_b" in res["comparison"]
    assert "rating_difference" in res["comparison"]


def test_grounding_validation():
    """Verify grounding validator flags unverified movie titles."""
    candidates = [
        {"title": "Inception", "genre_names": ["Sci-Fi"], "director_names": ["Christopher Nolan"]},
        {"title": "Arrival", "genre_names": ["Sci-Fi"], "director_names": ["Denis Villeneuve"]},
    ]

    # Grounded text
    grounded_text = "I recommend 'Inception' directed by Christopher Nolan."
    is_ok, violations = validate_grounding(grounded_text, candidates)
    assert is_ok is True
    assert len(violations) == 0

    # Hallucinated text
    hallucinated_text = "You should check out 'Avatar 7: Return to Pandora'!"
    is_ok, violations = validate_grounding(hallucinated_text, candidates)
    assert is_ok is False
    assert len(violations) > 0

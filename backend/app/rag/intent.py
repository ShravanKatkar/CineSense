import json
import re

import structlog

from app.core.config import get_settings
from app.recsys.hybrid.profile import UserTasteProfile
from app.schemas.ai import SearchIntent

log = structlog.get_logger()
settings = get_settings()

GENRE_KEYWORDS = {
    "action": "Action",
    "adventure": "Adventure",
    "animation": "Animation",
    "animated": "Animation",
    "comedy": "Comedy",
    "funny": "Comedy",
    "crime": "Crime",
    "documentary": "Documentary",
    "drama": "Drama",
    "family": "Family",
    "fantasy": "Fantasy",
    "history": "History",
    "historical": "History",
    "horror": "Horror",
    "scary": "Horror",
    "music": "Music",
    "musical": "Music",
    "mystery": "Mystery",
    "romance": "Romance",
    "romantic": "Romance",
    "sci-fi": "Science Fiction",
    "scifi": "Science Fiction",
    "science fiction": "Science Fiction",
    "thriller": "Thriller",
    "war": "War",
    "western": "Western",
}


def rule_based_intent_parser(query: str) -> SearchIntent:
    """Fallback local intent parser extracting genres, year ranges, runtime, and similar titles."""
    q_lower = query.lower()
    genres_inc: set[str] = set()

    for kw, genre_name in GENRE_KEYWORDS.items():
        if kw in q_lower:
            genres_inc.add(genre_name)

    year_min, year_max = None, None
    # 90s, 80s, 2000s matching
    if "90s" in q_lower or "1990s" in q_lower:
        year_min, year_max = 1990, 1999
    elif "80s" in q_lower or "1980s" in q_lower:
        year_min, year_max = 1980, 1989
    elif "2000s" in q_lower:
        year_min, year_max = 2000, 2009
    elif "2010s" in q_lower:
        year_min, year_max = 2010, 2019
    else:
        # Match explicit 4-digit years
        years = [int(y) for y in re.findall(r"\b(19\d\d|20\d\d)\b", query)]
        if len(years) == 1:
            if "after" in q_lower or "since" in q_lower:
                year_min = years[0]
            elif "before" in q_lower:
                year_max = years[0]
            else:
                year_min, year_max = years[0], years[0]
        elif len(years) >= 2:
            year_min, year_max = min(years), max(years)

    # Runtime matching: "under 2 hours", "short", "less than 90 mins"
    runtime_max = None
    if "under 2 hours" in q_lower or "under 120" in q_lower or "short" in q_lower:
        runtime_max = 120
    elif "under 90" in q_lower or "90 mins" in q_lower:
        runtime_max = 90

    # Extract similar_to titles: "like Inception", "similar to Interstellar"
    similar_to: list[str] = []
    sim_match = re.search(r"(?:like|similar to)\s+([A-Z][a-z0-9\s]+)", query)
    if sim_match:
        similar_to.append(sim_match.group(1).strip())

    cleaned_query = re.sub(
        r"\b(movies|films|show me|find|recommend|like|similar to|from the|in the|under|before|after)\b",
        "",
        q_lower,
    ).strip()

    return SearchIntent(
        semantic_query=cleaned_query or query,
        similar_to_titles=similar_to,
        genres_include=sorted(genres_inc),  # type: ignore
        year_min=year_min,
        year_max=year_max,
        runtime_max=runtime_max,
        confidence=0.85,
    )


async def parse_user_intent(query: str, user_profile: UserTasteProfile | None = None) -> SearchIntent:
    """Parses natural language query into structured SearchIntent schema."""
    anthropic_key = settings.anthropic_api_key.get_secret_value()

    if not anthropic_key or anthropic_key == "your_anthropic_api_key_here":
        log.info("using_rule_based_intent_parser", query=query)
        return rule_based_intent_parser(query)

    try:
        import anthropic

        client = anthropic.AsyncAnthropic(api_key=anthropic_key)
        system_prompt = (
            "You are an expert movie search query parser. Parse the user query into a JSON SearchIntent object.\n"
            "Respond ONLY with valid JSON matching the SearchIntent schema. No markdown wrapping."
        )

        response = await client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=400,
            system=system_prompt,
            messages=[{"role": "user", "content": f"Parse this query into SearchIntent JSON: '{query}'"}],
        )

        block = response.content[0]
        content = getattr(block, "text", "").strip()
        data = json.loads(content)
        return SearchIntent.model_validate(data)
    except Exception as exc:  # noqa: BLE001
        log.warning("llm_intent_parsing_failed_falling_back", error=str(exc))
        return rule_based_intent_parser(query)

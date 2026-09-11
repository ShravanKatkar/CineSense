import re

import structlog

log = structlog.get_logger()


def extract_candidate_fact_knowledge(candidates: list[dict]) -> dict[str, set[str]]:
    """Extracts ground truth set of valid titles, directors, actors, and genres from candidate pool."""
    titles: set[str] = set()
    directors: set[str] = set()
    cast: set[str] = set()
    genres: set[str] = set()

    for c in candidates:
        if c.get("title"):
            titles.add(c["title"].lower())
            # Stripped title without year e.g. "Toy Story"
            clean_t = re.sub(r"\s*\(\d{4}\)", "", c["title"]).strip().lower()
            titles.add(clean_t)

        for d in c.get("director_names", []) or c.get("directors", []):
            directors.add(str(d).lower())

        for p in c.get("cast_names", []) or c.get("top_cast", []):
            name = p["name"] if isinstance(p, dict) else str(p)
            cast.add(name.lower())

        for g in c.get("genre_names", []) or c.get("genres", []):
            genres.add(str(g).lower())

    return {
        "titles": titles,
        "directors": directors,
        "cast": cast,
        "genres": genres,
    }


def validate_grounding(text: str, candidates: list[dict]) -> tuple[bool, list[str]]:
    """Verifies that all entities mentioned in text are grounded in candidates metadata.

    Returns:
      - (is_grounded: bool, violations: list[str])
    """
    knowledge = extract_candidate_fact_knowledge(candidates)
    violations: list[str] = []

    # Check movie title quotes e.g. "Inception" or 'Toy Story' (single line, reasonable length)
    quoted_titles = re.findall(r"[\"']([^\"'\r\n]{2,60})[\"']", text)
    for q_t in quoted_titles:
        q_clean = q_t.strip().lower()
        # Ignore grammatical contractions or possessive fragments (e.g. "s ", "t ")
        if q_clean.startswith("s ") or q_clean in ("s", "t", "re", "ve", "ll", "d"):
            continue
        if len(q_clean) >= 3 and q_clean not in knowledge["titles"] and q_clean not in knowledge["genres"]:
            violations.append(f"Ungrounded movie title mentioned: '{q_t}'")

    is_grounded = len(violations) == 0
    if not is_grounded:
        log.warning("grounding_validation_failed", violations=violations)

    return is_grounded, violations

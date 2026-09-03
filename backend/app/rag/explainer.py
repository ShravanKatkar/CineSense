import json
from typing import Any

import structlog

from app.core.config import get_settings
from app.rag.grounding import validate_grounding
from app.recsys.hybrid.profile import UserTasteProfile
from app.schemas.ai import AssistantReply, Pick

log = structlog.get_logger()
settings = get_settings()


def safe_list(val: Any) -> list:
    if val is None:
        return []
    if isinstance(val, (list, tuple)):
        return list(val)
    if hasattr(val, "tolist"):
        return val.tolist()
    if hasattr(val, "__iter__"):
        return list(val)
    return []


def build_template_explanation(candidate: dict, query: str) -> str:
    genres = safe_list(candidate.get("genre_names")) or safe_list(candidate.get("genres"))
    g_str = ", ".join(str(g) for g in genres[:2]) if genres else "drama"
    vote_avg = candidate.get("vote_average", 7.5)

    return f"A highly rated {g_str} ({vote_avg}/10) matching your interest in '{query}'."


async def generate_grounded_explanations(
    query: str,
    candidates: list[dict],
    user_profile: UserTasteProfile | None = None,
) -> tuple[str, list[Pick], list[str], int]:
    """Generates a grounded natural language intro, item picks, caveats, and violation count.

    Returns: (intro, picks, caveats, violation_count)
    """
    anthropic_key = settings.anthropic_api_key.get_secret_value()
    violation_count = 0

    if not anthropic_key or anthropic_key == "your_anthropic_api_key_here":
        # Deterministic offline template generation
        intro = f"Here are top movies matching '{query}' from our catalogue:"
        picks: list[Pick] = []

        for c in candidates:
            mid = int(c.get("id") or c.get("movielens_id") or 0)
            why = build_template_explanation(c, query)
            aspects = [str(g) for g in (safe_list(c.get("genre_names")) or safe_list(c.get("genres")))][:3]
            picks.append(Pick(movie_id=mid, why=why, matched_aspects=aspects))

        return intro, picks, [], 0

    # Online Anthropic Claude LLM generation
    cand_summaries = []
    for c in candidates:
        mid = int(c.get("id") or c.get("movielens_id") or 0)
        cand_summaries.append({
            "movie_id": mid,
            "title": c.get("title"),
            "overview": c.get("overview"),
            "genres": safe_list(c.get("genre_names")) or safe_list(c.get("genres")),
            "directors": safe_list(c.get("director_names")) or safe_list(c.get("directors")),
            "vote_average": float(c.get("vote_average", 0.0)) if c.get("vote_average") is not None else None,
        })

    prompt_content = {
        "query": query,
        "candidates": cand_summaries,
    }

    system_prompt = (
        "You are CineSense, a grounded movie recommendation AI assistant.\n"
        "RULES:\n"
        "1. Recommend ONLY movies from the provided candidates list.\n"
        "2. Do NOT invent or mention any external titles, actors, or plot details not in the candidate list.\n"
        "3. Output strictly valid JSON matching AssistantReply schema (intro, picks, caveats, follow_up)."
    )

    try:
        import anthropic

        client = anthropic.AsyncAnthropic(api_key=anthropic_key)
        response = await client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=800,
            system=system_prompt,
            messages=[{"role": "user", "content": f"Generate AssistantReply JSON for: {json.dumps(prompt_content)}"}],
        )

        block = response.content[0]
        content_str = getattr(block, "text", "").strip()
        data = json.loads(content_str)
        reply = AssistantReply.model_validate(data)

        # Validate grounding across LLM output
        full_text = reply.intro + " " + " ".join(p.why for p in reply.picks)
        is_grounded, violations = validate_grounding(full_text, candidates)

        if not is_grounded:
            violation_count = len(violations)
            log.warning("replacing_ungrounded_picks_with_template_fallback", violations=violations)

            # Fallback to grounded template reasons for ungrounded picks
            for p in reply.picks:
                cand_match = next((c for c in candidates if int(c.get("id", 0)) == p.movie_id), None)
                if cand_match:
                    p.why = build_template_explanation(cand_match, query)

        return reply.intro, reply.picks, reply.caveats, violation_count

    except Exception as exc:  # noqa: BLE001
        log.warning("llm_explanation_generation_failed", error=str(exc))
        intro = f"Here are recommendations matching '{query}':"
        picks = [
            Pick(
                movie_id=int(c.get("id") or 0),
                why=build_template_explanation(c, query),
                matched_aspects=[str(g) for g in (safe_list(c.get("genre_names")) or safe_list(c.get("genres")))],
            )
            for c in candidates
        ]
        return intro, picks, [], 0

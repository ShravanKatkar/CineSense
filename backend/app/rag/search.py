"""
RAG Search — TMDB-backed candidate retrieval.

Pipeline:
  1. Parse user intent (rule-based fallback if no Anthropic key)
  2. Fetch candidates from TMDB using intent constraints
  3. Re-rank by match quality
  4. Generate grounded explanations (template fallback if no Anthropic key)
"""

from __future__ import annotations

import asyncio
import time
from typing import Any

import structlog

from app.core.paths import MOVIES_PARQUET
from app.rag.explainer import generate_grounded_explanations
from app.rag.intent import parse_user_intent
from app.recsys.hybrid.profile import UserTasteProfile
from app.schemas.ai import AISearchItemOut, AISearchMeta, AISearchResponse
from app.services import tmdb as tmdb_svc

log = structlog.get_logger()

# ── TMDB Genre Name → ID map (reverse of _GENRE_MAP in tmdb.py) ─────────────
_GENRE_NAME_TO_ID: dict[str, int] = {
    "action": 28, "adventure": 12, "animation": 16, "comedy": 35,
    "crime": 80, "documentary": 99, "drama": 18, "family": 10751,
    "fantasy": 14, "history": 36, "horror": 27, "music": 10402,
    "mystery": 9648, "romance": 10749, "science fiction": 878, "sci-fi": 878,
    "thriller": 53, "tv movie": 10770, "war": 10752, "western": 37,
}


def _genre_to_id(name: str) -> int | None:
    return _GENRE_NAME_TO_ID.get(name.lower())


def _normalise_genre(g: str) -> str:
    """Normalise TMDB genre names for consistent matching."""
    g_lower = g.lower().strip()
    _ALIASES = {
        "sci-fi": "science fiction",
        "science fiction": "science fiction",
        "sci fi": "science fiction",
    }
    return _ALIASES.get(g_lower, g_lower)


def _score_candidate(movie: dict, intent) -> float:
    """Simple relevance score: genre overlap + rating."""
    score = movie.get("vote_average", 0.0) or 0.0

    target_genres = set(_normalise_genre(g) for g in (intent.genres_include or []))
    movie_genres  = set(_normalise_genre(g) for g in (movie.get("genre_names") or movie.get("genres") or []))
    if target_genres:
        overlap = len(target_genres & movie_genres)
        score += overlap * 2.5  # stronger boost for genre match

    # Penalise excluded genres
    excl_genres = set(_normalise_genre(g) for g in (intent.genres_exclude or []))
    if excl_genres & movie_genres:
        score -= 4.0

    # Year range match boost
    release_date = str(movie.get("release_date") or "")
    if release_date and len(release_date) >= 4:
        try:
            yr = int(release_date[:4])
            if intent.year_min and yr < intent.year_min:
                score -= 3.0
            if intent.year_max and yr > intent.year_max:
                score -= 3.0
        except ValueError:
            pass

    # Minimum rating filter
    if intent.min_rating and (movie.get("vote_average") or 0) < intent.min_rating:
        score -= 5.0

    return score


async def _fetch_tmdb_candidates(intent, k: int) -> list[dict]:
    """Gather candidates from multiple TMDB sources and deduplicate."""
    tasks: list[Any] = []

    # Always fetch via semantic search if there's a good query
    q = intent.semantic_query or ""
    if q and len(q) > 2:
        tasks.append(tmdb_svc.search(q, page=1))

    # Fetch via discover for each genre constraint
    for genre_name in (intent.genres_include or []):
        gid = _genre_to_id(genre_name)
        sort_map = {
            "top_rated": "vote_average.desc",
            "newest":    "release_date.desc",
            "popular":   "popularity.desc",
        }
        tmdb_sort = sort_map.get(intent.sort_hint, "popularity.desc")
        year = intent.year_min if intent.year_min == intent.year_max else None
        tasks.append(tmdb_svc.discover(genre_id=gid, sort_by=tmdb_sort, year=year))

    # If no genre specified, use discover with sort
    if not intent.genres_include:
        sort_map = {
            "top_rated": "vote_average.desc",
            "newest":    "release_date.desc",
            "popular":   "popularity.desc",
        }
        tmdb_sort = sort_map.get(intent.sort_hint, "popularity.desc")
        tasks.append(tmdb_svc.discover(sort_by=tmdb_sort))

    # Also try similar-title seeding
    for title in (intent.similar_to_titles or [])[:2]:
        tasks.append(tmdb_svc.search(title, page=1))

    # Run all fetches in parallel
    results = await asyncio.gather(*tasks, return_exceptions=True)

    # Merge and deduplicate by tmdb id
    seen: set[int] = set()
    merged: list[dict] = []
    for batch in results:
        if isinstance(batch, Exception):
            log.warning("tmdb_fetch_error", error=str(batch))
            continue
        for movie in (batch or []):
            mid = movie.get("id", 0)
            if mid and mid not in seen:
                seen.add(mid)
                merged.append(movie)

    return merged


async def perform_rag_search(
    query: str,
    user_id: int | None = None,
    k: int = 12,
    user_profile: UserTasteProfile | None = None,
) -> AISearchResponse:
    start_t = time.perf_counter()
    log.info("rag_search_start", query=query, user_id=user_id, k=k)

    degraded = False
    degraded_reason: str | None = None

    # ── 1. Intent Parsing ────────────────────────────────────────────────────
    intent = await parse_user_intent(query, user_profile=user_profile)
    log.info("intent_parsed", genres=intent.genres_include, year_min=intent.year_min, semantic=intent.semantic_query)

    # ── 2. Candidate Retrieval from TMDB ─────────────────────────────────────
    try:
        candidates_raw = await _fetch_tmdb_candidates(intent, k=k)
    except Exception as exc:
        log.error("tmdb_candidate_fetch_failed", error=str(exc))
        candidates_raw = []
        degraded = True
        degraded_reason = "TMDB candidate retrieval failed"

    # ── 3. Local parquet enrichment (optional) ───────────────────────────────
    # If parquet is available, we can also fold in its candidates
    if MOVIES_PARQUET.exists() and not candidates_raw:
        try:
            import pandas as pd
            df = pd.read_parquet(MOVIES_PARQUET)
            df["id"] = df["movielens_id"].dropna().astype(int)
            q_lower = intent.semantic_query.lower()
            matches = df[df["title"].str.lower().str.contains(q_lower, na=False)]
            for _, row in matches.head(k).iterrows():
                candidates_raw.append(row.to_dict())
        except Exception as exc:
            log.warning("parquet_fallback_failed", error=str(exc))

    if not candidates_raw:
        # Ultimate fallback: popular movies
        try:
            candidates_raw = await tmdb_svc.get_popular(page=1)
            degraded = True
            degraded_reason = "No candidates matched query; showing popular movies"
        except Exception:
            pass

    # ── 4. Score & Rank candidates ───────────────────────────────────────────
    scored = [(m, _score_candidate(m, intent)) for m in candidates_raw]
    scored.sort(key=lambda x: x[1], reverse=True)

    # Hard genre filter: when genres_include is set, only keep movies that match at least one
    if intent.genres_include:
        target_genres = set(_normalise_genre(g) for g in intent.genres_include)
        genre_matched = [
            (m, s) for (m, s) in scored
            if set(_normalise_genre(g) for g in (m.get("genre_names") or m.get("genres") or [])) & target_genres
        ]
        # If the genre filter is too aggressive (< 3 results), relax it
        if len(genre_matched) >= 3:
            scored = genre_matched

    # Apply runtime filter after scoring
    if intent.runtime_max:
        scored = [(m, s) for (m, s) in scored if (m.get("runtime") or 999) <= intent.runtime_max]

    # Apply year range filter
    if intent.year_min or intent.year_max:
        def _get_year(m: dict) -> int | None:
            rd = str(m.get("release_date") or "")
            try:
                return int(rd[:4]) if len(rd) >= 4 else None
            except ValueError:
                return None

        year_filtered = []
        for (m, s) in scored:
            yr = _get_year(m)
            if yr is None:
                continue  # Skip movies with no date when filtering by year
            if intent.year_min and yr < intent.year_min:
                continue
            if intent.year_max and yr > intent.year_max:
                continue
            year_filtered.append((m, s))

        # Relax year filter only if it leaves too few results
        if len(year_filtered) >= 3:
            scored = year_filtered

    candidates: list[dict] = [m for (m, _) in scored[:k]]

    # ── 5. Grounded Explanation Generation ──────────────────────────────────
    intro, picks, caveats, violations = await generate_grounded_explanations(
        query=query,
        candidates=candidates,
        user_profile=user_profile,
    )

    pick_map = {p.movie_id: p for p in picks}

    # ── 6. Build output items ────────────────────────────────────────────────
    items: list[AISearchItemOut] = []
    for c in candidates:
        m_dict = dict(c)
        mid = int(c.get("id") or c.get("tmdb_id") or 0)
        p = pick_map.get(mid)
        if p:
            m_dict["why"] = p.why
            m_dict["matched_aspects"] = p.matched_aspects
        m_dict["score"] = _score_candidate(c, intent)
        m_dict["sources"] = {}

        # Ensure schema compatibility — alias genre_names if only genres present
        if not m_dict.get("genre_names") and m_dict.get("genres"):
            m_dict["genre_names"] = m_dict["genres"]
        if not m_dict.get("tmdb_id"):
            m_dict["tmdb_id"] = mid

        try:
            items.append(AISearchItemOut.model_validate(m_dict))
        except Exception as exc:
            log.warning("ai_item_validation_failed", error=str(exc), title=m_dict.get("title"))

    elapsed_ms = int((time.perf_counter() - start_t) * 1000)

    meta = AISearchMeta(
        cached=False,
        degraded=degraded,
        degraded_reason=degraded_reason,
        latency_ms=elapsed_ms,
        cost_usd=0.0001,
        candidates_considered=len(candidates_raw),
        grounding_violations=violations,
    )

    all_caveats = caveats + list(intent.unsupported_constraints)
    if degraded and degraded_reason:
        all_caveats.append(degraded_reason)

    return AISearchResponse(
        query=query,
        intent=intent,
        intro=intro,
        items=items,
        caveats=all_caveats,
        meta=meta,
    )

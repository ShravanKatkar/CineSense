import time
from typing import Any

import pandas as pd
import structlog

from app.core.paths import MOVIES_PARQUET
from app.rag.explainer import generate_grounded_explanations
from app.rag.intent import parse_user_intent
from app.recsys.base import MovieFilters
from app.recsys.hybrid.profile import UserTasteProfile
from app.recsys.hybrid.recommender import HybridRecommender
from app.schemas.ai import AISearchItemOut, AISearchMeta, AISearchResponse

log = structlog.get_logger()


def get_movies_df() -> pd.DataFrame:
    if not MOVIES_PARQUET.exists():
        raise FileNotFoundError(f"Missing {MOVIES_PARQUET}.")
    df = pd.read_parquet(MOVIES_PARQUET)
    df["id"] = df["movielens_id"].dropna().astype(int)
    return df


async def perform_rag_search(
    query: str,
    user_id: int | None = None,
    k: int = 12,
    user_profile: UserTasteProfile | None = None,
) -> AISearchResponse:
    start_t = time.perf_counter()
    log.info("starting_rag_search", query=query, user_id=user_id, k=k)

    # 1. Intent Parsing
    intent = await parse_user_intent(query, user_profile=user_profile)

    # Convert intent constraints to MovieFilters
    filters = MovieFilters(
        genres_include=[str(g) for g in intent.genres_include],
        genres_exclude=[str(g) for g in intent.genres_exclude],
        year_min=intent.year_min,
        year_max=intent.year_max,
        runtime_max=intent.runtime_max,
    )

    # 2. Candidate Retrieval via Hybrid Recommender
    hybrid = HybridRecommender()
    movies_df = get_movies_df()

    # Find seed IDs if intent specifies similar_to_titles
    seed_ids: list[int] = []
    for title in intent.similar_to_titles:
        matches = movies_df[movies_df["title"].str.lower().str.contains(title.lower(), na=False)]
        if not matches.empty:
            seed_ids.append(int(matches.iloc[0]["id"]))

    scored_recs = hybrid.recommend(
        user_id=user_id,
        seed_ids=seed_ids,
        filters=filters,
        k=k * 2,
        apply_mmr=True,
    )

    candidate_mids = [r.movie_id for r in scored_recs]
    cand_df = movies_df[movies_df["id"].isin(candidate_mids)].head(k)
    candidates: list[dict[str, Any]] = [row.to_dict() for _, row in cand_df.iterrows()]

    # 3. Grounded Explanation Generation
    intro, picks, caveats, violations = await generate_grounded_explanations(
        query=query,
        candidates=candidates,
        user_profile=user_profile,
    )

    pick_map = {p.movie_id: p for p in picks}

    items: list[AISearchItemOut] = []
    for c in candidates:
        m_dict = dict(c)
        mid = int(c.get("id", 0))
        p = pick_map.get(mid)

        if p:
            m_dict["why"] = p.why
            m_dict["matched_aspects"] = p.matched_aspects

        items.append(AISearchItemOut.model_validate(m_dict))

    elapsed_ms = int((time.perf_counter() - start_t) * 1000)

    meta = AISearchMeta(
        cached=False,
        degraded=False,
        latency_ms=elapsed_ms,
        cost_usd=0.0001 if violations == 0 else 0.0002,
        candidates_considered=len(candidates),
        grounding_violations=violations,
    )

    return AISearchResponse(
        query=query,
        intent=intent,
        intro=intro,
        items=items,
        caveats=caveats + intent.unsupported_constraints,
        meta=meta,
    )

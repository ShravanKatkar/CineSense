from datetime import UTC, datetime
from pathlib import Path

import pandas as pd
from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import get_optional_user
from app.db.session import get_db_session
from app.models.users import Rating, User
from app.recsys.baseline.popularity import PopularityRecommender
from app.recsys.hybrid.profile import compute_user_profile
from app.recsys.hybrid.recommender import HybridRecommender, generate_template_reason
from app.schemas.recommendations import (
    RecommendationFeedOut,
    RecommendationRowOut,
    ScoredMovieItemOut,
)

router = APIRouter(prefix="/recommendations", tags=["Recommendations"])
PROCESSED_DIR = Path("data/processed")
MOVIES_PARQUET = PROCESSED_DIR / "movies.parquet"


def get_movies_dict() -> dict[int, dict]:
    if not MOVIES_PARQUET.exists():
        return {}
    df = pd.read_parquet(MOVIES_PARQUET)
    df["id"] = df["movielens_id"].dropna().astype(int)
    return {int(row["id"]): row.to_dict() for _, row in df.iterrows()}


@router.get("/for-you", response_model=RecommendationFeedOut)
async def get_for_you_feed(
    current_user: User | None = Depends(get_optional_user),
    session: AsyncSession = Depends(get_db_session),
):
    movies_dict = get_movies_dict()
    hybrid = HybridRecommender()
    rows: list[RecommendationRowOut] = []

    if current_user is None:
        # Anonymous user feed -> Popularity + Genre rows
        pop_recs = hybrid.pop_rec.recommend(k=12)
        pop_items: list[ScoredMovieItemOut] = []
        for r in pop_recs:
            if r.movie_id in movies_dict:
                m_data = dict(movies_dict[r.movie_id])
                m_data["score"] = r.score
                m_data["reason"] = "Top rated classic across all viewers"
                pop_items.append(ScoredMovieItemOut.model_validate(m_data))

        rows.append(RecommendationRowOut(title="Top Rated Classics", strategy="popularity", items=pop_items))

        return RecommendationFeedOut(
            rows=rows,
            strategy="anonymous_popularity",
            cold_start=True,
            generated_at=datetime.now(UTC),
        )

    # Fetch user's rating history
    r_result = await session.execute(
        select(Rating).where(Rating.user_id == current_user.id).order_by(Rating.rating.desc(), Rating.updated_at.desc())
    )
    user_ratings = list(r_result.scalars().all())

    user_ratings_df = pd.DataFrame([{"userId": r.user_id, "movieId": r.movie_id, "rating": float(r.rating)} for r in user_ratings])
    movies_df = pd.read_parquet(MOVIES_PARQUET)
    profile = compute_user_profile(current_user.id, user_ratings_df, movies_df)

    seed_ids = [r.movie_id for r in user_ratings if r.rating >= 4.0][:5]

    # Primary personalization row
    hybrid_recs = hybrid.recommend(
        user_id=current_user.id,
        seed_ids=seed_ids,
        k=12,
        apply_mmr=True,
    )

    primary_items: list[ScoredMovieItemOut] = []
    for r in hybrid_recs:
        if r.movie_id in movies_dict:
            m_data = dict(movies_dict[r.movie_id])
            m_data["score"] = r.score
            m_data["sources"] = r.sources
            seed_title = movies_dict[seed_ids[0]]["title"] if seed_ids and seed_ids[0] in movies_dict else None
            m_data["reason"] = generate_template_reason(r.sources, seed_title)
            primary_items.append(ScoredMovieItemOut.model_validate(m_data))

    rows.append(
        RecommendationRowOut(
            title="Picked For You",
            strategy="hybrid_rrf",
            items=primary_items,
        )
    )

    # Secondary "Because you liked [Fav Title]" row if seeds exist
    if seed_ids and seed_ids[0] in movies_dict:
        seed_id = seed_ids[0]
        seed_title = movies_dict[seed_id]["title"]
        because_recs = hybrid.recommend(seed_ids=[seed_id], k=12, apply_mmr=True)

        because_items: list[ScoredMovieItemOut] = []
        for r in because_recs:
            if r.movie_id in movies_dict:
                m_data = dict(movies_dict[r.movie_id])
                m_data["score"] = r.score
                m_data["reason"] = f"Similar themes & style to {seed_title}"
                because_items.append(ScoredMovieItemOut.model_validate(m_data))

        rows.append(
            RecommendationRowOut(
                title=f"Because You Liked {seed_title}",
                seed_movie_id=seed_id,
                strategy="seed_similarity",
                items=because_items,
            )
        )

    return RecommendationFeedOut(
        rows=rows,
        strategy=profile.recommendation_strategy,
        cold_start=profile.cold_start,
        generated_at=datetime.now(UTC),
    )


@router.get("/cold-start", response_model=list[ScoredMovieItemOut])
async def get_cold_start_onboarding(k: int = Query(20, ge=10, le=40)):
    """Returns a diverse set of 20 recognizable movies across different genres for quick user onboarding."""
    pop = PopularityRecommender()
    recs = pop.recommend(k=k * 4)

    movies_dict = get_movies_dict()
    items: list[ScoredMovieItemOut] = []
    seen_genres: set[str] = set()

    for r in recs:
        if r.movie_id in movies_dict:
            m_data = dict(movies_dict[r.movie_id])
            g_list = m_data.get("genre_names", [])
            primary_g = g_list[0] if (isinstance(g_list, (list, tuple)) or hasattr(g_list, "__len__")) and len(g_list) > 0 else "General"

            # Prefer items that cover new genres
            if primary_g not in seen_genres or len(items) >= k // 2:
                seen_genres.add(primary_g)
                m_data["reason"] = f"Rate this to personalize your feed ({primary_g})"
                items.append(ScoredMovieItemOut.model_validate(m_data))

            if len(items) >= k:
                break

    return items

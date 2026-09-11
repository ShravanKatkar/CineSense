from datetime import UTC, datetime

import pandas as pd
from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import get_optional_user
from app.core.paths import MOVIES_PARQUET
from app.db.session import get_db_session
from app.models.users import Rating, User
from app.recsys.baseline.popularity import PopularityRecommender
from app.recsys.hybrid.profile import compute_user_profile
from app.recsys.hybrid.recommender import HybridRecommender, generate_template_reason
from app.schemas.recommendations import (
    MovieNightCompromiseItem,
    MovieNightRequest,
    MovieNightResponse,
    RecommendationFeedOut,
    RecommendationRowOut,
    ScoredMovieItemOut,
    WatchTonightRequest,
    WatchTonightResponse,
)
from app.schemas.telemetry import (
    FeedbackResponse,
    InteractionFeedbackIn,
    SessionTuneRequest,
)

router = APIRouter(prefix="/recommendations", tags=["Recommendations"])


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
        from app.services import tmdb as tmdb_svc

        # 1. Live TMDB Trending Row
        try:
            tmdb_rows = await tmdb_svc.get_trending("week")
            if not tmdb_rows:
                tmdb_rows = await tmdb_svc.get_popular(page=1)

            pop_items: list[ScoredMovieItemOut] = []
            for r in tmdb_rows[:12]:
                try:
                    r_copy = dict(r)
                    r_copy["score"] = float(r.get("popularity") or 0.0)
                    r_copy["reason"] = "Trending this week on TMDB"
                    pop_items.append(ScoredMovieItemOut.model_validate(r_copy))
                except Exception:
                    pass

            if pop_items:
                rows.append(RecommendationRowOut(title="Trending Now", strategy="tmdb_trending", items=pop_items))
        except Exception:
            pass

        # 2. Top Rated Classics from local recommender
        try:
            pop_recs = hybrid.pop_rec.recommend(k=12)
            pop_items_local: list[ScoredMovieItemOut] = []
            for r in pop_recs:
                if r.movie_id in movies_dict:
                    m_data = {k: v.tolist() if hasattr(v, "tolist") else v for k, v in movies_dict[r.movie_id].items()}
                    m_data["score"] = r.score
                    m_data["reason"] = "Top rated classic across all viewers"
                    pop_items_local.append(ScoredMovieItemOut.model_validate(m_data))

            if pop_items_local:
                rows.append(RecommendationRowOut(title="Top Rated Classics", strategy="popularity", items=pop_items_local))
        except Exception:
            pass

        return RecommendationFeedOut(
            rows=rows,
            strategy="anonymous_discovery",
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
async def get_cold_start_onboarding(k: int = Query(20, ge=1, le=40)):
    """Returns a diverse set of 20 recognizable movies across different genres for quick user onboarding."""
    pop = PopularityRecommender()
    recs = pop.recommend(k=k * 4)

    movies_dict = get_movies_dict()
    items: list[ScoredMovieItemOut] = []
    seen_genres: set[str] = set()

    for r in recs:
        if r.movie_id in movies_dict:
            m_data = {k: v.tolist() if hasattr(v, "tolist") else v for k, v in movies_dict[r.movie_id].items()}
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


@router.post("/wizard", response_model=WatchTonightResponse)
async def watch_tonight_wizard(req: WatchTonightRequest):
    """
    Curates a focused 3-movie selection based on tonight's available time, mood, company, and language.
    """
    movies_dict = get_movies_dict()
    if not movies_dict:
        from app.services import tmdb as tmdb_svc
        tmdb_items = await tmdb_svc.get_popular(page=1)
        res_items = []
        for r in tmdb_items[:3]:
            r["score"] = r.get("vote_average", 7.5)
            r["reason"] = f"Top trending selection for tonight's {req.mood} vibe."
            res_items.append(ScoredMovieItemOut.model_validate(r))
        return WatchTonightResponse(
            night_vibe_summary=f"Selected for a {req.mood} evening ({req.available_time} watch).",
            recommendations=res_items,
            criteria_echo=req.model_dump(),
        )

    mood_genres = {
        "thrilling": {"Action", "Thriller", "Crime", "Mystery"},
        "feel_good": {"Comedy", "Romance", "Animation", "Adventure"},
        "deep": {"Drama", "History", "Biography"},
        "mind_bending": {"Sci-Fi", "Mystery", "Thriller"},
        "scary": {"Horror", "Thriller", "Mystery"},
    }.get(req.mood.lower(), {"Action", "Drama", "Comedy"})

    company_bonus = {
        "solo": {"Sci-Fi", "Drama", "Thriller"},
        "date_night": {"Romance", "Comedy", "Drama", "Thriller"},
        "friends": {"Comedy", "Action", "Adventure", "Horror"},
        "family": {"Family", "Animation", "Comedy", "Adventure"},
    }.get(req.company.lower(), set())

    candidates = []
    for mid, m in movies_dict.items():
        g_list = m.get("genre_names", [])
        genres = set(g_list) if hasattr(g_list, "__iter__") and not isinstance(g_list, (str, bytes)) else set()
        runtime = m.get("runtime") or 110
        lang = m.get("original_language", "en")
        vote_avg = float(m.get("vote_average") or 6.5)
        pop = float(m.get("popularity") or 10.0)

        # Runtime filter
        if req.available_time == "quick" and runtime > 105:
            continue
        if req.available_time == "epic" and runtime < 115:
            continue

        # Language filter
        if req.language and req.language.lower() != "any" and lang and lang.lower() != req.language.lower():
            continue

        # Family safety filter
        if req.company.lower() == "family":
            if any(bad in genres for bad in ["Horror", "War"]) and not any(ok in genres for ok in ["Animation", "Family"]):
                continue

        mood_matches = len(genres & mood_genres)
        company_matches = len(genres & company_bonus)
        score = (mood_matches * 3.0) + (company_matches * 1.5) + (vote_avg * 0.8) + min(pop / 10.0, 3.0)

        if mood_matches > 0 or len(candidates) < 20:
            candidates.append((score, m, runtime, list(genres)))

    candidates.sort(key=lambda x: x[0], reverse=True)

    results: list[ScoredMovieItemOut] = []
    for score, m, runtime, genres in candidates[:3]:
        m_data = {k: v.tolist() if hasattr(v, "tolist") else v for k, v in m.items()}
        m_data["score"] = round(score, 2)
        primary_g = genres[0] if genres else "Cinema"
        m_data["reason"] = (
            f"Matches your {req.mood} mood ({runtime}m, {primary_g}) with a {m_data.get('vote_average', 7.5)}/10 score."
        )
        results.append(ScoredMovieItemOut.model_validate(m_data))

    mood_labels = {
        "thrilling": "high-octane thrill",
        "feel_good": "uplifting & relaxed",
        "deep": "thought-provoking & emotional",
        "mind_bending": "cerebral & mind-bending",
        "scary": "spine-chilling horror",
    }
    vibe_desc = mood_labels.get(req.mood.lower(), req.mood)
    company_desc = req.company.replace("_", " ").title()

    return WatchTonightResponse(
        night_vibe_summary=f"Curated for a {vibe_desc} evening • {company_desc} • {req.available_time.title()} duration",
        recommendations=results,
        criteria_echo=req.model_dump(),
    )


@router.post("/movie-night", response_model=MovieNightResponse)
async def movie_night_group(req: MovieNightRequest):
    """
    AI Group Movie Night: Combines multiple participant profiles using
    Least Misery + Average Relevance preference aggregation to maximize group enjoyment.
    """
    movies_dict = get_movies_dict()
    participants = req.participants

    all_genres_sets = [set(p.favorite_genres) for p in participants if p.favorite_genres]
    if len(all_genres_sets) >= 2:
        pair_jaccards = []
        for i in range(len(all_genres_sets)):
            for j in range(i + 1, len(all_genres_sets)):
                union = len(all_genres_sets[i] | all_genres_sets[j])
                inter = len(all_genres_sets[i] & all_genres_sets[j])
                pair_jaccards.append(inter / max(union, 1))
        avg_jaccard = sum(pair_jaccards) / max(len(pair_jaccards), 1)
        compatibility_score = int(round(50 + avg_jaccard * 50))
    else:
        compatibility_score = 75

    scored_candidates = []
    for mid, m in movies_dict.items():
        g_list = m.get("genre_names", [])
        m_genres = set(g_list) if hasattr(g_list, "__iter__") and not isinstance(g_list, (str, bytes)) else set()
        vote_avg = float(m.get("vote_average") or 6.5)

        p_scores = []
        appeal_map = {}
        for p in participants:
            p_favs = {g.lower() for g in p.favorite_genres}
            m_genres_lower = {g.lower() for g in m_genres}
            matches = m_genres_lower & p_favs
            if matches:
                p_satisfaction = min(10.0, 7.0 + len(matches) * 1.5)
                matched_str = ", ".join(list(matches)[:2]).title()
                appeal_map[p.name] = f"Matches your love for {matched_str}"
            else:
                p_satisfaction = 4.5
                appeal_map[p.name] = f"Universal crowd-pleaser ({vote_avg}/10 rating)"
            p_scores.append(p_satisfaction)

        avg_score = sum(p_scores) / len(p_scores)
        min_score = min(p_scores)
        compromise_score = round(0.65 * avg_score + 0.35 * min_score, 2)

        scored_candidates.append((compromise_score, m, appeal_map, min_score, avg_score))

    scored_candidates.sort(key=lambda x: x[0], reverse=True)

    consensus_recs: list[MovieNightCompromiseItem] = []
    for comp_score, m, appeal_map, min_s, avg_s in scored_candidates[:6]:
        m_data = {k: v.tolist() if hasattr(v, "tolist") else v for k, v in m.items()}
        m_data["score"] = comp_score
        m_data["compromise_score"] = comp_score
        m_data["appeal_per_participant"] = appeal_map
        p_names = ", ".join(p.name for p in participants[:2])
        m_data["reason"] = f"Highest mutual agreement score ({comp_score}/10) with zero misery penalty for {p_names}."
        consensus_recs.append(MovieNightCompromiseItem.model_validate(m_data))

    names_list = " & ".join(p.name for p in participants)
    explanation = (
        f"Consensus achieved for {names_list} with a {compatibility_score}% taste compatibility rating. "
        f"The top recommendations maximize group enjoyment using Least-Misery aggregation."
    )

    return MovieNightResponse(
        group_compatibility_score=compatibility_score,
        consensus_recommendations=consensus_recs,
        explanation=explanation,
    )


# ── Real-Time Feedback & Telemetry Store ─────────────────────────────────────

_TELEMETRY_EVENTS: list[dict] = []
_MAX_TELEMETRY_EVENTS = 5000


@router.post("/feedback", response_model=FeedbackResponse)
async def record_feedback(payload: InteractionFeedbackIn):
    """Store implicit interaction telemetry (clicks, trailer plays, drawer views, ratings)."""
    import uuid

    event_id = str(uuid.uuid4())
    evt = {
        "id": event_id,
        "event_type": payload.event_type,
        "movie_id": payload.movie_id,
        "session_id": payload.session_id or "anonymous",
        "metadata": payload.metadata,
        "timestamp": payload.timestamp or datetime.now(UTC),
    }

    _TELEMETRY_EVENTS.append(evt)
    if len(_TELEMETRY_EVENTS) > _MAX_TELEMETRY_EVENTS:
        del _TELEMETRY_EVENTS[: len(_TELEMETRY_EVENTS) - _MAX_TELEMETRY_EVENTS]

    return FeedbackResponse(
        status="recorded",
        event_id=event_id,
        session_total=len(_TELEMETRY_EVENTS),
    )


@router.get("/feedback/metrics")
async def get_feedback_metrics():
    """Retrieve real-time interaction telemetry for the evaluation dashboard."""
    from collections import Counter

    total_events = len(_TELEMETRY_EVENTS)
    event_counts = Counter(e["event_type"] for e in _TELEMETRY_EVENTS)
    unique_movies = len({e["movie_id"] for e in _TELEMETRY_EVENTS})
    unique_sessions = len({e.get("session_id") for e in _TELEMETRY_EVENTS if e.get("session_id")})

    top_movie_ids = [mid for mid, _ in Counter(e["movie_id"] for e in _TELEMETRY_EVENTS).most_common(5)]

    # Compute quick CTR proxy if impressions and clicks exist
    clicks = event_counts.get("click", 0) + event_counts.get("drawer_view", 0)
    impressions = max(total_events, 1)
    ctr_est = round((clicks / impressions) * 100, 2)

    return {
        "total_interactions": total_events,
        "event_breakdown": dict(event_counts),
        "unique_movies_explored": unique_movies,
        "active_sessions": max(unique_sessions, 1),
        "realtime_engagement_rate_pct": ctr_est,
        "top_explored_movie_ids": top_movie_ids,
        "last_event_at": _TELEMETRY_EVENTS[-1]["timestamp"].isoformat() if _TELEMETRY_EVENTS else None,
    }


@router.post("/session-tune", response_model=list[ScoredMovieItemOut])
async def session_tune(body: SessionTuneRequest):
    """Dynamically re-rank and generate recommendations based on active session seeds."""
    if not body.seed_ids:
        return []

    movies_dict = get_movies_dict()
    hybrid = HybridRecommender()

    # Use the most recent session seeds
    active_seeds = [sid for sid in body.seed_ids if sid in movies_dict][-4:]
    if not active_seeds:
        # Fall back to using any seed
        active_seeds = body.seed_ids[-3:]

    # Hybrid recommend using active session seeds
    try:
        tuned_recs = hybrid.recommend(seed_ids=active_seeds, k=body.k, apply_mmr=True)
    except Exception:
        tuned_recs = []

    out: list[ScoredMovieItemOut] = []
    seen_ids = set(active_seeds)

    for r in tuned_recs:
        if r.movie_id in movies_dict and r.movie_id not in seen_ids:
            seen_ids.add(r.movie_id)
            m_data = dict(movies_dict[r.movie_id])
            m_data["score"] = r.score
            m_data["sources"] = r.sources
            primary_seed_title = movies_dict[active_seeds[-1]]["title"] if active_seeds and active_seeds[-1] in movies_dict else "recent views"
            m_data["reason"] = f"Real-time session tune: shares tone & themes with {primary_seed_title}"
            out.append(ScoredMovieItemOut.model_validate(m_data))

    if not out and active_seeds:
        # Fallback to TMDB recommendations for active seed
        from app.services import tmdb as tmdb_svc
        try:
            primary_seed = active_seeds[-1]
            tmdb_similar = await tmdb_svc.get_similar(primary_seed)
            for m in tmdb_similar[:body.k]:
                if m.get("id") not in seen_ids:
                    seen_ids.add(m.get("id"))
                    m_copy = dict(m)
                    m_copy["score"] = float(m.get("popularity") or 7.0)
                    m_copy["reason"] = "Live session affinity match"
                    out.append(ScoredMovieItemOut.model_validate(m_copy))
        except Exception:
            pass

    return out[:body.k]



"""
Movies API — data served live from TMDB v3.
Falls back to the local movies.parquet file when present, but TMDB is
always tried first so real poster images and up-to-date metadata are used.
"""

from __future__ import annotations

import pandas as pd
from fastapi import APIRouter, Query

from app.core.exceptions import NotFoundError
from app.core.paths import MOVIES_PARQUET
from app.schemas.movies import (
    MovieCompareRequest,
    MovieCompareResponse,
    MovieDetailOut,
    MovieMetricComparison,
    MovieOut,
    PaginatedMoviesOut,
)
from app.services import tmdb as tmdb_svc

router = APIRouter(prefix="/movies", tags=["Movies"])


# ── Parquet helpers (optional local data) ────────────────────────────────────

def _parquet_available() -> bool:
    return MOVIES_PARQUET.exists()


def _parquet_df() -> pd.DataFrame:
    df = pd.read_parquet(MOVIES_PARQUET)
    df["id"] = df["movielens_id"].dropna().astype(int)
    return df


def _rows_to_movie_out(rows: list[dict]) -> list[MovieOut]:
    out = []
    for r in rows:
        try:
            out.append(MovieOut.model_validate(r))
        except Exception:
            pass
    return out


def _rows_to_detail_out(rows: list[dict]) -> list[MovieDetailOut]:
    out = []
    for r in rows:
        try:
            out.append(MovieDetailOut.model_validate(r))
        except Exception:
            pass
    return out


# ── Endpoints ─────────────────────────────────────────────────────────────────


@router.get("", response_model=PaginatedMoviesOut)
async def list_movies(
    genre: str | None = None,
    language: str | None = Query(None, description="ISO 639-1 language code e.g. hi, mr, te, ta, en"),
    year_min: int | None = None,
    year_max: int | None = None,
    sort_by: str = Query("popularity", enum=["popularity", "weighted_rating", "release_date", "vote_average"]),
    page: int = Query(1, ge=1),
    page_size: int = Query(40, ge=1, le=100),
):
    """List movies with optional genre / language / year filters — uses local parquet or TMDB."""
    if _parquet_available() and not language:
        df = _parquet_df()
        if genre:
            g_lower = genre.lower()
            df = df[df["genre_names"].apply(
                lambda g_list: any(g_lower == str(g).lower() for g in g_list) if hasattr(g_list, "__iter__") else False
            )]
        if year_min:
            df = df[pd.to_numeric(df["release_date"].astype(str).str[:4], errors="coerce") >= year_min]
        if year_max:
            df = df[pd.to_numeric(df["release_date"].astype(str).str[:4], errors="coerce") <= year_max]

        if sort_by == "popularity":
            df = df.sort_values(by="popularity", ascending=False)
        elif sort_by in ("weighted_rating", "vote_average"):
            df = df.sort_values(by="weighted_rating", ascending=False)
        elif sort_by == "release_date":
            df = df.sort_values(by="release_date", ascending=False)

        total = len(df)
        start = (page - 1) * page_size
        end = start + page_size
        page_df = df.iloc[start:end]

        rows = [{k: v.tolist() if hasattr(v, "tolist") else v for k, v in row.to_dict().items()} for _, row in page_df.iterrows()]
        items = _rows_to_movie_out(rows)
        return PaginatedMoviesOut(
            items=items,
            page=page,
            page_size=page_size,
            total=total,
            has_next=end < total,
        )

    # Fallback to TMDB for language-specific queries (Indian cinema) or when parquet is absent
    tmdb_sort = {
        "popularity":     "popularity.desc",
        "weighted_rating":"vote_average.desc",
        "release_date":   "release_date.desc",
        "vote_average":   "vote_average.desc",
    }.get(sort_by, "popularity.desc")

    genre_id: int | None = None
    if genre:
        genre_id = _genre_name_to_id(genre)

    rows = await tmdb_svc.discover(
        genre_id=genre_id,
        sort_by=tmdb_sort,
        page=page,
        with_original_language=language,
    )

    if year_min or year_max:
        def _year(r: dict) -> int | None:
            d = r.get("release_date") or ""
            try:
                return int(str(d)[:4])
            except Exception:
                return None
        rows = [r for r in rows if _in_year_range(_year(r), year_min, year_max)]

    items = _rows_to_movie_out(rows)
    return PaginatedMoviesOut(
        items=items,
        page=page,
        page_size=page_size,
        total=len(items),
        has_next=len(items) == page_size,
    )


@router.get("/popular", response_model=list[MovieOut])
async def get_popular_movies(k: int = Query(20, ge=1, le=100)):
    """Return popular movies from live TMDB (or local parquet fallback)."""
    try:
        results: list[dict] = []
        page = 1
        while len(results) < k and page <= 3:
            batch = await tmdb_svc.get_popular(page=page)
            if not batch:
                break
            results.extend(batch)
            page += 1
        if results:
            return _rows_to_movie_out(results[:k])
    except Exception:
        pass

    if _parquet_available():
        df = _parquet_df()
        has_poster = ~df["poster_path"].astype(str).str.contains("placeholder|none|^$", case=False, na=True)
        valid_df = df[has_poster]
        if valid_df.empty:
            valid_df = df
        pop_df = valid_df.sort_values(by="popularity", ascending=False).head(k)
        rows = [{k: v.tolist() if hasattr(v, "tolist") else v for k, v in row.to_dict().items()} for _, row in pop_df.iterrows()]
        return _rows_to_movie_out(rows)

    return []


@router.get("/trending", response_model=list[MovieOut])
async def get_trending_movies(time_window: str = Query("week", enum=["day", "week"])):
    """Return trending movies from TMDB."""
    rows = await tmdb_svc.get_trending(time_window=time_window)
    return _rows_to_movie_out(rows)


@router.get("/upcoming", response_model=list[MovieOut])
async def get_upcoming_movies(page: int = Query(1, ge=1, le=10)):
    """Return upcoming theatrical and streaming releases from TMDB."""
    rows = await tmdb_svc.get_upcoming(page=page)
    return _rows_to_movie_out(rows)


@router.get("/search", response_model=list[MovieOut])
async def search_movies(
    q: str = Query(..., min_length=1),
    limit: int = Query(20, ge=1, le=100),
):
    """Full-text search via TMDB (or parquet fallback)."""
    if _parquet_available():
        df = _parquet_df()
        q_lower = q.lower()
        title_matches = df[df["title"].astype(str).str.lower().str.contains(q_lower, na=False)]
        overview_matches = df[df["overview"].astype(str).str.lower().str.contains(q_lower, na=False)]
        combined = pd.concat([title_matches, overview_matches]).drop_duplicates(subset=["id"])
        combined = combined.sort_values(by="popularity", ascending=False).head(limit)
        rows = [{k: v.tolist() if hasattr(v, "tolist") else v for k, v in row.to_dict().items()} for _, row in combined.iterrows()]
        return _rows_to_movie_out(rows)

    results: list[dict] = []
    page = 1
    while len(results) < limit:
        batch = await tmdb_svc.search(query=q, page=page)
        if not batch:
            break
        results.extend(batch)
        page += 1

    return _rows_to_movie_out(results[:limit])


@router.get("/meta/genres", response_model=list[str])
async def list_genres():
    """Return all genre names from TMDB."""
    genres = await tmdb_svc.get_genres()
    if genres:
        return genres
    if _parquet_available():
        df = _parquet_df()
        all_genres: set[str] = set()
        for g_list in df.get("genre_names", []):
            if isinstance(g_list, (list, tuple)):
                all_genres.update(g_list)
        return sorted(all_genres)
def _compute_movie_metrics(movie: MovieDetailOut) -> MovieMetricComparison:
    genres = {g.lower() for g in movie.genres}
    runtime = movie.runtime or 110
    rating = movie.vote_average or 7.0
    vote_count = movie.vote_count or 1000

    # 1. Pacing: 0-10
    base_pacing = 6.0
    if runtime < 100:
        base_pacing += 1.5
    elif runtime > 145:
        base_pacing -= 1.5
    if any(g in genres for g in ["action", "thriller", "animation", "comedy"]):
        base_pacing += 1.5
    if any(g in genres for g in ["drama", "history", "biography"]):
        base_pacing -= 1.0
    pacing = max(2.0, min(9.8, round(base_pacing, 1)))

    # 2. Visual Spectacle: 0-10
    spectacle = 4.0
    if any(g in genres for g in ["sci-fi", "science fiction", "fantasy", "adventure"]):
        spectacle += 3.5
    if "action" in genres or "animation" in genres:
        spectacle += 1.5
    if vote_count > 5000:
        spectacle += 0.5
    visual_spectacle = max(2.5, min(9.9, round(spectacle, 1)))

    # 3. Emotional Depth: 0-10
    depth = 4.5
    if "drama" in genres:
        depth += 2.5
    if any(g in genres for g in ["romance", "biography", "history"]):
        depth += 1.5
    if any(g in genres for g in ["action", "horror"]) and "drama" not in genres:
        depth -= 1.0
    emotional_depth = max(2.0, min(9.9, round(depth, 1)))

    # 4. Story Complexity: 0-10
    complexity = 4.5
    if "mystery" in genres:
        complexity += 2.5
    if any(g in genres for g in ["sci-fi", "science fiction", "crime"]):
        complexity += 1.5
    if "thriller" in genres:
        complexity += 1.0
    if any(g in genres for g in ["comedy", "family", "animation"]) and "sci-fi" not in genres:
        complexity -= 1.5
    story_complexity = max(2.0, min(9.8, round(complexity, 1)))

    # 5. Rewatchability: 0-10
    rewatch = 5.0 + (rating - 6.0) * 0.8
    if any(g in genres for g in ["comedy", "action", "adventure", "animation"]):
        rewatch += 1.5
    if "horror" in genres or ("drama" in genres and runtime > 150):
        rewatch -= 1.0
    rewatchability = max(3.0, min(9.9, round(rewatch, 1)))

    return MovieMetricComparison(
        pacing=pacing,
        visual_spectacle=visual_spectacle,
        emotional_depth=emotional_depth,
        story_complexity=story_complexity,
        rewatchability=rewatchability,
    )


async def _generate_comparison_analysis(
    movie_a: MovieDetailOut,
    movie_b: MovieDetailOut,
    metrics_a: MovieMetricComparison,
    metrics_b: MovieMetricComparison,
) -> tuple[list[str], dict[str, str], str]:
    import json
    from app.core.config import get_settings
    from groq import AsyncGroq

    settings = get_settings()
    key = settings.groq_api_key.get_secret_value() if hasattr(settings, "groq_api_key") else ""
    if key and "your_groq_api_key" not in key:
        try:
            client = AsyncGroq(api_key=key)
            prompt = f"""You are an elite cinema analyst and curator. Compare these two films head-to-head:
Film A: "{movie_a.title}" ({str(movie_a.release_date)[:4]}, Genres: {', '.join(movie_a.genres)}, Runtime: {movie_a.runtime or 110}m, Rating: {movie_a.vote_average or 7.5}/10)
Overview: {movie_a.overview or 'No synopsis'}

Film B: "{movie_b.title}" ({str(movie_b.release_date)[:4]}, Genres: {', '.join(movie_b.genres)}, Runtime: {movie_b.runtime or 110}m, Rating: {movie_b.vote_average or 7.5}/10)
Overview: {movie_b.overview or 'No synopsis'}

Provide a JSON response with:
1. "tradeoffs": array of 3 distinct bullet points comparing pacing, tone, and cinematic scale.
2. "winner_for_mood": dictionary mapping 3 moods (e.g. "Adrenaline Rush", "Emotional Storytelling", "Intellectual Challenge") to either "{movie_a.title}" or "{movie_b.title}".
3. "ai_verdict": 2-sentence decisive conclusion on who should watch which film.
Format: JSON only."""
            resp = await client.chat.completions.create(
                model=settings.groq_model,
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"},
                temperature=0.3,
                max_tokens=600,
            )
            raw = resp.choices[0].message.content or "{}"
            parsed = json.loads(raw)
            tradeoffs = parsed.get("tradeoffs", [])
            winner_for_mood = parsed.get("winner_for_mood", {})
            ai_verdict = parsed.get("ai_verdict", "")
            if tradeoffs and ai_verdict:
                return tradeoffs, winner_for_mood, ai_verdict
        except Exception:
            pass

    # High-quality deterministic fallback
    tradeoffs = [
        f"**Pacing & Intensity**: {movie_a.title} ({metrics_a.pacing}/10) provides a {'fast and punchy' if metrics_a.pacing >= 7 else 'deliberate'} rhythm compared to {movie_b.title}'s ({metrics_b.pacing}/10) cadence.",
        f"**Visual Scope**: {movie_a.title} scores {metrics_a.visual_spectacle}/10 in spectacle versus {movie_b.title}'s {metrics_b.visual_spectacle}/10 rating.",
        f"**Thematic Focus**: {movie_a.title} emphasizes {', '.join(movie_a.genres[:2]) or 'cinematic depth'}, while {movie_b.title} delivers on {', '.join(movie_b.genres[:2]) or 'engaging drama'}.",
    ]
    winner_for_mood = {
        "High Spectacle & Scale": movie_a.title if metrics_a.visual_spectacle >= metrics_b.visual_spectacle else movie_b.title,
        "Emotional Depth": movie_a.title if metrics_a.emotional_depth >= metrics_b.emotional_depth else movie_b.title,
        "Complex Storytelling": movie_a.title if metrics_a.story_complexity >= metrics_b.story_complexity else movie_b.title,
    }
    ai_verdict = (
        f"Choose {movie_a.title} if you want {', '.join(movie_a.genres[:2]) or 'a gripping watch'} with high visual impact. "
        f"Pick {movie_b.title} if you are seeking {', '.join(movie_b.genres[:2]) or 'a character-driven journey'} with a {movie_b.runtime or 110}-minute runtime."
    )
    return tradeoffs, winner_for_mood, ai_verdict


@router.post("/compare", response_model=MovieCompareResponse)
async def compare_movies_endpoint(req: MovieCompareRequest):
    """Compare two movies head-to-head with multi-dimensional metrics and AI tradeoff analysis."""
    detail_a = await get_movie_detail(req.movie_id_a)
    detail_b = await get_movie_detail(req.movie_id_b)

    metrics_a = _compute_movie_metrics(detail_a)
    metrics_b = _compute_movie_metrics(detail_b)

    tradeoffs, winner_for_mood, verdict = await _generate_comparison_analysis(
        detail_a, detail_b, metrics_a, metrics_b
    )

    return MovieCompareResponse(
        movie_a=detail_a,
        movie_b=detail_b,
        metrics_a=metrics_a,
        metrics_b=metrics_b,
        tradeoffs=tradeoffs,
        winner_for_mood=winner_for_mood,
        ai_verdict=verdict,
    )


@router.get("/{movie_id}", response_model=MovieDetailOut)
async def get_movie_detail(movie_id: int):
    """Fetch full movie detail (with cast, keywords) from local parquet or TMDB."""
    if _parquet_available():
        df = _parquet_df()
        match_df = df[df["id"] == movie_id]
        if not match_df.empty:
            row = {k: v.tolist() if hasattr(v, "tolist") else v for k, v in match_df.iloc[0].to_dict().items()}
            poster_path = row.get("poster_path")
            backdrop_path = row.get("backdrop_path")
            if poster_path and not row.get("poster_url"):
                row["poster_url"] = f"https://image.tmdb.org/t/p/w342{poster_path}"
            if backdrop_path and not row.get("backdrop_url"):
                row["backdrop_url"] = f"https://image.tmdb.org/t/p/w1280{backdrop_path}"
            return MovieDetailOut.model_validate(row)

    detail = await tmdb_svc.get_detail(movie_id)
    if detail is None:
        raise NotFoundError(f"Movie with ID {movie_id} not found.", identifier=str(movie_id))
    return MovieDetailOut.model_validate(detail)


@router.get("/{movie_id}/similar", response_model=list[MovieOut])
async def get_similar_movies(movie_id: int, k: int = Query(12, ge=1, le=50)):
    """Return similar movies using Hybrid RecSys or TMDB."""
    if _parquet_available():
        try:
            from app.recsys.hybrid.recommender import HybridRecommender
            hybrid = HybridRecommender()
            scored = hybrid.recommend(seed_ids=[movie_id], k=k)
            if scored:
                mid_order = [r.movie_id for r in scored]
                df = _parquet_df()
                matched_df = df[df["id"].isin(mid_order)].copy()
                matched_df["sort_idx"] = matched_df["id"].apply(lambda m: mid_order.index(m) if m in mid_order else 999)
                matched_df = matched_df.sort_values(by="sort_idx")
                rows = [{k: v.tolist() if hasattr(v, "tolist") else v for k, v in row.to_dict().items()} for _, row in matched_df.iterrows()]
                return _rows_to_movie_out(rows)
        except Exception:
            pass

    rows = await tmdb_svc.get_similar(movie_id, page=1)
    if not rows:
        rows = await tmdb_svc.get_recommendations(movie_id, page=1)
    if not rows:
        raise NotFoundError(f"No similar movies found for {movie_id}.", identifier=str(movie_id))
    return _rows_to_movie_out(rows[:k])


@router.get("/{movie_id}/videos")
async def get_movie_videos(movie_id: int):
    """Fetch official YouTube trailers and video teasers for a movie."""
    tmdb_id = movie_id
    if _parquet_available():
        df = _parquet_df()
        match_df = df[df["id"] == movie_id]
        if not match_df.empty and pd.notna(match_df.iloc[0].get("tmdb_id")):
            tmdb_id = int(match_df.iloc[0]["tmdb_id"])

    videos = await tmdb_svc.get_videos(tmdb_id)
    return {"movie_id": movie_id, "tmdb_id": tmdb_id, "videos": videos}


@router.get("/{movie_id}/watch-providers")
async def get_movie_watch_providers(movie_id: int, country: str = Query("US", min_length=2, max_length=2)):
    """Fetch streaming and rental providers (Netflix, Prime, etc.) for a movie."""
    tmdb_id = movie_id
    if _parquet_available():
        df = _parquet_df()
        match_df = df[df["id"] == movie_id]
        if not match_df.empty and pd.notna(match_df.iloc[0].get("tmdb_id")):
            tmdb_id = int(match_df.iloc[0]["tmdb_id"])

    providers = await tmdb_svc.get_watch_providers(tmdb_id, country_code=country.upper())
    return providers




# ── Utilities ─────────────────────────────────────────────────────────────────

# Reverse map: lowercase genre name → tmdb genre id
_NAME_TO_ID: dict[str, int] = {v.lower(): k for k, v in tmdb_svc._GENRE_MAP.items()}

def _genre_name_to_id(name: str) -> int | None:
    return _NAME_TO_ID.get(name.lower())


def _in_year_range(year: int | None, y_min: int | None, y_max: int | None) -> bool:
    if year is None:
        return True
    if y_min and year < y_min:
        return False
    if y_max and year > y_max:
        return False
    return True

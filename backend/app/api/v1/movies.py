from pathlib import Path

import pandas as pd
from fastapi import APIRouter, Depends, Query

from app.api.v1.deps import PaginationParams, get_optional_user
from app.core.exceptions import NotFoundError
from app.core.paths import MOVIES_PARQUET
from app.models.users import User
from app.recsys.baseline.popularity import PopularityRecommender
from app.recsys.hybrid.recommender import HybridRecommender
from app.schemas.movies import MovieDetailOut, MovieOut, PaginatedMoviesOut

router = APIRouter(prefix="/movies", tags=["Movies"])


def get_movies_df() -> pd.DataFrame:
    if not MOVIES_PARQUET.exists():
        raise NotFoundError("movies.parquet data file not found.", identifier="movies.parquet")
    df = pd.read_parquet(MOVIES_PARQUET)
    df["id"] = df["movielens_id"].dropna().astype(int)
    return df


@router.get("", response_model=PaginatedMoviesOut)
async def list_movies(
    genre: str | None = None,
    year_min: int | None = None,
    year_max: int | None = None,
    certification: str | None = None,
    sort_by: str = Query("popularity", enum=["popularity", "weighted_rating", "release_date", "vote_average"]),
    pagination: PaginationParams = Depends(),
    user: User | None = Depends(get_optional_user),
):
    df = get_movies_df()

    if genre:
        g_lower = genre.lower()
        df = df[df["genre_names"].apply(lambda g_list: any(g_lower == str(g).lower() for g in g_list))]

    if year_min or year_max:
        dates = df["release_date"].astype(str)
        years = dates.str[:4]
        valid_years = pd.to_numeric(years, errors="coerce")
        if year_min:
            df = df[valid_years >= year_min]
        if year_max:
            df = df[valid_years <= year_max]

    if certification:
        df = df[df["certification"].str.upper() == certification.upper()]

    if sort_by == "popularity":
        df = df.sort_values(by="popularity", ascending=False)
    elif sort_by == "weighted_rating":
        pop = PopularityRecommender()
        df = pop.sorted_df
    elif sort_by == "release_date":
        df = df.sort_values(by="release_date", ascending=False)
    elif sort_by == "vote_average":
        df = df.sort_values(by="vote_average", ascending=False)

    total = len(df)
    start = (pagination.page - 1) * pagination.page_size
    end = start + pagination.page_size
    page_df = df.iloc[start:end]

    items = [MovieOut.model_validate(row.to_dict()) for _, row in page_df.iterrows()]
    return PaginatedMoviesOut(
        items=items,
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
        has_next=end < total,
    )


@router.get("/popular", response_model=list[MovieOut])
async def get_popular_movies(k: int = Query(20, ge=1, le=50)):
    pop = PopularityRecommender()
    recs = pop.recommend(k=k)
    mid_order = [r.movie_id for r in recs]

    df = get_movies_df()
    matched_df = df[df["id"].isin(mid_order)].copy()
    matched_df["sort_idx"] = matched_df["id"].apply(lambda m: mid_order.index(m) if m in mid_order else 999)
    matched_df = matched_df.sort_values(by="sort_idx")

    return [MovieOut.model_validate(row.to_dict()) for _, row in matched_df.iterrows()]


@router.get("/search", response_model=list[MovieOut])
async def search_movies(
    q: str = Query(..., min_length=1),
    limit: int = Query(20, ge=1, le=100),
):
    df = get_movies_df()
    q_lower = q.lower()

    title_matches = df[df["title"].str.lower().str.contains(q_lower, na=False)]
    overview_matches = df[df["overview"].str.lower().str.contains(q_lower, na=False)]

    combined = pd.concat([title_matches, overview_matches]).drop_duplicates(subset=["id"])
    combined = combined.sort_values(by="popularity", ascending=False).head(limit)

    return [MovieOut.model_validate(row.to_dict()) for _, row in combined.iterrows()]


@router.get("/meta/genres", response_model=list[str])
async def list_genres():
    df = get_movies_df()
    all_genres: set[str] = set()
    for g_list in df["genre_names"]:
        if isinstance(g_list, (list, tuple)):
            all_genres.update(g_list)
    return sorted(all_genres)


@router.get("/{movie_id}", response_model=MovieDetailOut)
async def get_movie_detail(movie_id: int):
    df = get_movies_df()
    match_df = df[df["id"] == movie_id]

    if match_df.empty:
        raise NotFoundError(f"Movie with ID {movie_id} not found.", identifier=str(movie_id))

    row = match_df.iloc[0].to_dict()
    return MovieDetailOut.model_validate(row)


@router.get("/{movie_id}/similar", response_model=list[MovieOut])
async def get_similar_movies(movie_id: int, k: int = Query(12, ge=1, le=50)):
    hybrid = HybridRecommender()
    scored = hybrid.recommend(seed_ids=[movie_id], k=k)

    if not scored:
        raise NotFoundError(f"No similar recommendations found for movie ID {movie_id}.", identifier=str(movie_id))

    mid_order = [r.movie_id for r in scored]
    df = get_movies_df()
    matched_df = df[df["id"].isin(mid_order)].copy()
    matched_df["sort_idx"] = matched_df["id"].apply(lambda m: mid_order.index(m) if m in mid_order else 999)
    matched_df = matched_df.sort_values(by="sort_idx")

    return [MovieOut.model_validate(row.to_dict()) for _, row in matched_df.iterrows()]

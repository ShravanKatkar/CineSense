from pathlib import Path

import pandas as pd
from pydantic import BaseModel

PROCESSED_DIR = Path("data/processed")
ML_DIR = Path("data/raw/ml-latest-small")


class GenrePreference(BaseModel):
    name: str
    count: int
    mean_rating: float


class DirectorPreference(BaseModel):
    name: str
    count: int


class UserTasteProfile(BaseModel):
    user_id: int
    n_ratings: int
    n_favorites: int
    mean_rating: float
    top_genres: list[GenrePreference]
    top_directors: list[DirectorPreference]
    disliked_genres: list[str]
    recommendation_strategy: str
    cold_start: bool


def compute_user_profile(user_id: int, user_ratings_df: pd.DataFrame, movies_df: pd.DataFrame) -> UserTasteProfile:
    """Computes compact user taste profile from rating history and movies metadata."""
    u_ratings = user_ratings_df[user_ratings_df["userId"] == user_id]
    n_ratings = len(u_ratings)

    if n_ratings == 0:
        return UserTasteProfile(
            user_id=user_id,
            n_ratings=0,
            n_favorites=0,
            mean_rating=0.0,
            top_genres=[],
            top_directors=[],
            disliked_genres=[],
            recommendation_strategy="popularity_by_genre",
            cold_start=True,
        )

    mean_r = float(u_ratings["rating"].mean())
    fav_count = int((u_ratings["rating"] >= 4.0).sum())

    merged = u_ratings.merge(movies_df, left_on="movieId", right_on="movielens_id", how="inner")

    # Genre preferences
    genre_stats: dict[str, list[float]] = {}
    for _, row in merged.iterrows():
        genres = row.get("genre_names", [])
        if isinstance(genres, (list, tuple)):
            for g in genres:
                genre_stats.setdefault(g, []).append(float(row["rating"]))

    top_genres: list[GenrePreference] = []
    disliked_genres: list[str] = []

    for g, ratings_list in genre_stats.items():
        avg_g = sum(ratings_list) / len(ratings_list)
        if len(ratings_list) >= 2 and avg_g >= 3.8:
            top_genres.append(GenrePreference(name=g, count=len(ratings_list), mean_rating=round(avg_g, 2)))
        elif len(ratings_list) >= 2 and avg_g <= 2.5:
            disliked_genres.append(g)

    top_genres.sort(key=lambda gp: -gp.count)

    # Director preferences
    director_counts: dict[str, int] = {}
    for _, row in merged[merged["rating"] >= 4.0].iterrows():
        directors = row.get("director_names", [])
        if isinstance(directors, (list, tuple)):
            for d in directors:
                director_counts[d] = director_counts.get(d, 0) + 1

    top_directors = [
        DirectorPreference(name=d, count=c)
        for d, c in sorted(director_counts.items(), key=lambda kv: -kv[1])[:5]
    ]

    strategy = "hybrid" if n_ratings >= 5 else "content_embedding"
    cold_start = n_ratings < 5

    return UserTasteProfile(
        user_id=user_id,
        n_ratings=n_ratings,
        n_favorites=fav_count,
        mean_rating=round(mean_r, 2),
        top_genres=top_genres[:5],
        top_directors=top_directors,
        disliked_genres=disliked_genres[:5],
        recommendation_strategy=strategy,
        cold_start=cold_start,
    )

from pathlib import Path
from typing import NamedTuple
import numpy as np
import pandas as pd
from scipy.sparse import csr_matrix

ML_DIR = Path("data/raw/ml-latest-small")
PROCESSED_DIR = Path("data/processed")


class EvalDataset(NamedTuple):
    train_ratings: pd.DataFrame
    test_ratings: pd.DataFrame
    train_matrix: csr_matrix
    test_user_items: dict[int, set[int]]
    user_id_map: dict[int, int]  # raw userId -> matrix row index
    movie_id_map: dict[int, int]  # raw movieId -> matrix col index
    reverse_movie_map: dict[int, int]  # col index -> raw movieId
    n_users: int
    n_movies: int


def get_temporal_eval_split(test_k: int = 5, min_ratings: int = 10) -> EvalDataset:
    """Performs a temporal leave-last-k-out split over MovieLens ratings dataset."""
    ratings_path = ML_DIR / "ratings.csv"
    movies_path = PROCESSED_DIR / "movies.parquet"

    if not ratings_path.exists():
        raise FileNotFoundError(f"Missing {ratings_path}. Run download_movielens.py first.")
    if not movies_path.exists():
        raise FileNotFoundError(f"Missing {movies_path}. Run build_movies_table.py first.")

    ratings = pd.read_csv(ratings_path)
    movies = pd.read_parquet(movies_path)

    valid_movie_ids = set(movies["movielens_id"].dropna().astype(int))
    ratings = ratings[ratings["movieId"].isin(valid_movie_ids)].copy()

    # Filter users with at least min_ratings
    user_counts = ratings["userId"].value_counts()
    eligible_users = set(user_counts[user_counts >= min_ratings].index)
    ratings = ratings[ratings["userId"].isin(eligible_users)].copy()

    # Sort ratings temporally per user
    ratings.sort_values(by=["userId", "timestamp"], ascending=[True, True], inplace=True)

    # Build unique ID mappings
    unique_users = sorted(ratings["userId"].unique())
    unique_movies = sorted(movies["movielens_id"].dropna().astype(int).unique())

    user_id_map = {uid: idx for idx, uid in enumerate(unique_users)}
    movie_id_map = {mid: idx for idx, mid in enumerate(unique_movies)}
    reverse_movie_map = {idx: mid for mid, idx in movie_id_map.items()}

    n_users = len(unique_users)
    n_movies = len(unique_movies)

    # Leave-last-k-out split per user
    ratings["user_rank"] = ratings.groupby("userId").cumcount(ascending=False)
    test_mask = ratings["user_rank"] < test_k

    test_ratings = ratings[test_mask].copy()
    train_ratings = ratings[~test_mask].copy()

    # Filter positive test ratings (only 3.5+ stars count as hit targets)
    test_positive = test_ratings[test_ratings["rating"] >= 3.5]
    test_user_items: dict[int, set[int]] = {}
    for uid, group in test_positive.groupby("userId"):
        test_user_items[uid] = set(group["movieId"].astype(int))

    # Construct train CSR matrix
    train_rows = train_ratings["userId"].map(user_id_map).values
    train_cols = train_ratings["movieId"].map(movie_id_map).values
    train_vals = train_ratings["rating"].values.astype(np.float32)

    train_matrix = csr_matrix((train_vals, (train_rows, train_cols)), shape=(n_users, n_movies))

    return EvalDataset(
        train_ratings=train_ratings,
        test_ratings=test_ratings,
        train_matrix=train_matrix,
        test_user_items=test_user_items,
        user_id_map=user_id_map,
        movie_id_map=movie_id_map,
        reverse_movie_map=reverse_movie_map,
        n_users=n_users,
        n_movies=n_movies,
    )

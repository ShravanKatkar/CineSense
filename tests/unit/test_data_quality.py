from pathlib import Path
import pandas as pd

DATA_DIR = Path("data/raw/ml-latest-small")
PROCESSED_DIR = Path("data/processed")


def test_movielens_shape():
    assert (DATA_DIR / "ratings.csv").exists(), "ratings.csv must exist"
    assert (DATA_DIR / "movies.csv").exists(), "movies.csv must exist"
    assert (DATA_DIR / "links.csv").exists(), "links.csv must exist"

    ratings = pd.read_csv(DATA_DIR / "ratings.csv")
    movies = pd.read_csv(DATA_DIR / "movies.csv")

    assert len(ratings) == 100836, f"Expected 100,836 ratings, got {len(ratings)}"
    assert ratings["userId"].nunique() == 610, f"Expected 610 unique users, got {ratings['userId'].nunique()}"

    valid_ratings = {0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5, 5.0}
    actual_ratings = set(ratings["rating"].unique())
    assert actual_ratings.issubset(valid_ratings), f"Unexpected rating values: {actual_ratings - valid_ratings}"

    # Check for orphan ratings (movie_ids in ratings that don't exist in movies)
    movie_ids = set(movies["movieId"])
    rating_movie_ids = set(ratings["movieId"])
    orphan_movies = rating_movie_ids - movie_ids
    assert len(orphan_movies) == 0, f"Found orphan movie ratings: {orphan_movies}"


def test_tmdb_coverage():
    parquet_path = PROCESSED_DIR / "movies.parquet"
    assert parquet_path.exists(), "movies.parquet must exist"

    movies = pd.read_parquet(parquet_path)
    assert len(movies) >= 9000, f"Expected >= 9,000 movies in movies.parquet, got {len(movies)}"
    assert movies["title"].notna().all(), "All movies must have a title"
    assert movies["overview"].notna().mean() >= 0.95, "Overview coverage must be >= 95%"
    assert movies["poster_path"].notna().mean() >= 0.95, "Poster path coverage must be >= 95%"
    assert movies["tmdb_id"].duplicated().sum() == 0, "tmdb_id must be unique across all rows"

    # Runtime check for valid non-null runtimes
    non_null_runtimes = movies["runtime"].dropna()
    assert (non_null_runtimes > 0).all(), "All non-null runtimes must be > 0"

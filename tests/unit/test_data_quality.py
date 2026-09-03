from pathlib import Path
import pandas as pd

DATA_DIR = Path("data/raw/ml-latest-small")


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

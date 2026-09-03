from pathlib import Path

import pandas as pd
from app.recsys.base import MovieFilters, ScoredMovie

PROCESSED_DIR = Path("data/processed")


class PopularityRecommender:
    name = "popularity"

    def __init__(self, movies_path: Path = PROCESSED_DIR / "movies.parquet", percentile: float = 0.80):
        if not movies_path.exists():
            raise FileNotFoundError(f"Missing {movies_path}. Run build_movies_table.py first.")

        self.movies_df = pd.read_parquet(movies_path)
        self.movies_df["movie_id"] = self.movies_df["movielens_id"].dropna().astype(int)

        # Bayesian Weighted Rating
        C = float(self.movies_df["vote_average"].mean())
        m = float(self.movies_df["vote_count"].quantile(percentile))

        v = self.movies_df["vote_count"].values
        R = self.movies_df["vote_average"].values

        weighted_scores = (v / (v + m)) * R + (m / (v + m)) * C
        self.movies_df["weighted_rating"] = weighted_scores

        # Rank indices sorted by weighted rating DESC
        self.sorted_df = self.movies_df.sort_values(by="weighted_rating", ascending=False).reset_index(drop=True)

    def recommend(
        self,
        *,
        user_id: int | None = None,
        seed_ids: list[int] | None = None,
        filters: MovieFilters | None = None,
        k: int = 12,
    ) -> list[ScoredMovie]:
        df = self.sorted_df

        if seed_ids:
            df = df[~df["movie_id"].isin(seed_ids)]

        if filters:
            if filters.genres_include:
                inc_set = {g.lower() for g in filters.genres_include}
                df = df[df["genre_names"].apply(lambda g_list: bool(inc_set.intersection({g.lower() for g in g_list})))]
            if filters.year_min:
                df = df[df["release_date"].apply(lambda d: int(str(d)[:4]) >= filters.year_min if pd.notna(d) and str(d)[:4].isdigit() else False)]
            if filters.year_max:
                df = df[df["release_date"].apply(lambda d: int(str(d)[:4]) <= filters.year_max if pd.notna(d) and str(d)[:4].isdigit() else False)]

        top_k = df.head(k)
        results: list[ScoredMovie] = []
        for rank, (_, row) in enumerate(top_k.iterrows(), start=1):
            results.append(
                ScoredMovie(
                    movie_id=int(row["movie_id"]),
                    score=float(row["weighted_rating"]),
                    sources={"popularity": rank},
                )
            )
        return results

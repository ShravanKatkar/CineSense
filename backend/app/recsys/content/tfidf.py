from pathlib import Path

import numpy as np
import pandas as pd
from scipy.sparse import csr_matrix
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import linear_kernel

from app.core.paths import MOVIES_PARQUET
from app.recsys.base import MovieFilters, ScoredMovie


class TfidfRecommender:
    name = "tfidf"

    def __init__(self, movies_path: Path = MOVIES_PARQUET):
        if not movies_path.exists():
            raise FileNotFoundError(f"Missing {movies_path}. Run build_documents.py first.")

        self.movies_df = pd.read_parquet(movies_path)
        self.movies_df["movie_id"] = self.movies_df["movielens_id"].dropna().astype(int)

        self.movie_id_to_idx = {mid: idx for idx, mid in enumerate(self.movies_df["movie_id"])}
        self.idx_to_movie_id = {idx: mid for mid, idx in self.movie_id_to_idx.items()}

        documents = self.movies_df["document"].fillna("").tolist()

        self.vectorizer = TfidfVectorizer(
            stop_words="english",
            ngram_range=(1, 2),
            min_df=2,
            max_df=0.5,
            sublinear_tf=True,
            max_features=60_000,
        )
        self.tfidf_matrix: csr_matrix = self.vectorizer.fit_transform(documents)

    def similar_to_seed(self, seed_id: int, k: int = 150) -> list[tuple[int, float]]:
        if seed_id not in self.movie_id_to_idx:
            return []

        idx = self.movie_id_to_idx[seed_id]
        seed_vec = self.tfidf_matrix[idx]

        # Dot product cosine similarity against all items
        sims = linear_kernel(seed_vec, self.tfidf_matrix).ravel()

        top_k_indices = np.argpartition(-sims, min(k + 1, len(sims)))[: k + 1]
        sorted_top = top_k_indices[np.argsort(-sims[top_k_indices])]

        results: list[tuple[int, float]] = []
        for i in sorted_top:
            mid = self.idx_to_movie_id[i]
            if mid != seed_id:
                results.append((mid, float(sims[i])))
            if len(results) >= k:
                break

        return results

    def recommend(
        self,
        *,
        user_id: int | None = None,
        seed_ids: list[int] | None = None,
        filters: MovieFilters | None = None,
        k: int = 12,
    ) -> list[ScoredMovie]:
        if not seed_ids:
            return []

        candidate_scores: dict[int, float] = {}
        for seed in seed_ids:
            sims = self.similar_to_seed(seed, k=150)
            for mid, sim in sims:
                if mid not in seed_ids:
                    candidate_scores[mid] = max(candidate_scores.get(mid, 0.0), sim)

        sorted_cands = sorted(candidate_scores.items(), key=lambda kv: -kv[1])

        results: list[ScoredMovie] = []
        for rank, (mid, score) in enumerate(sorted_cands, start=1):
            results.append(
                ScoredMovie(
                    movie_id=mid,
                    score=score,
                    sources={"tfidf": rank},
                )
            )
            if len(results) >= k:
                break

        return results

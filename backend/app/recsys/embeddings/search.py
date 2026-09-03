import json
from pathlib import Path

import numpy as np
from app.recsys.base import MovieFilters, ScoredMovie

PROCESSED_DIR = Path("data/processed")
EMBEDDINGS_NPY = PROCESSED_DIR / "movie_embeddings.npy"
EMBEDDINGS_MAP = PROCESSED_DIR / "movie_embeddings_map.json"


class EmbeddingRecommender:
    name = "embedding"

    def __init__(
        self,
        embeddings_path: Path = EMBEDDINGS_NPY,
        map_path: Path = EMBEDDINGS_MAP,
    ):
        if not embeddings_path.exists() or not map_path.exists():
            raise FileNotFoundError("Missing embedding artifacts. Run embed_movies.py first.")

        self.embeddings: np.ndarray = np.load(embeddings_path)
        # Normalize rows to unit length for cosine dot product
        norms = np.linalg.norm(self.embeddings, axis=1, keepdims=True)
        norms[norms == 0] = 1.0
        self.embeddings = self.embeddings / norms

        raw_map: dict[str, int] = json.loads(map_path.read_text(encoding="utf-8"))
        self.movie_id_to_idx = {int(mid): idx for mid, idx in raw_map.items()}
        self.idx_to_movie_id = {idx: mid for mid, idx in self.movie_id_to_idx.items()}

    def similar_to_vector(self, query_vector: np.ndarray, k: int = 150) -> list[tuple[int, float]]:
        norm = np.linalg.norm(query_vector)
        if norm > 0:
            query_vector = query_vector / norm

        sims = self.embeddings @ query_vector
        top_k_idx = np.argpartition(-sims, min(k, len(sims)))[:k]
        sorted_top = top_k_idx[np.argsort(-sims[top_k_idx])]

        results: list[tuple[int, float]] = []
        for idx in sorted_top:
            mid = self.idx_to_movie_id[idx]
            results.append((mid, float(sims[idx])))
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

        seed_indices = [self.movie_id_to_idx[sid] for sid in seed_ids if sid in self.movie_id_to_idx]
        if not seed_indices:
            return []

        # Average seed embedding vector
        seed_vecs = self.embeddings[seed_indices]
        avg_vec = np.mean(seed_vecs, axis=0)

        similar_items = self.similar_to_vector(avg_vec, k=150)

        results: list[ScoredMovie] = []
        rank = 1
        for mid, score in similar_items:
            if mid not in seed_ids:
                results.append(
                    ScoredMovie(
                        movie_id=mid,
                        score=score,
                        sources={"embedding": rank},
                    )
                )
                rank += 1
            if len(results) >= k:
                break

        return results

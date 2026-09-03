from pathlib import Path

import pandas as pd

from app.recsys.base import MovieFilters, ScoredMovie
from app.recsys.baseline.popularity import PopularityRecommender
from app.recsys.collaborative.als import ALSRecommender
from app.recsys.collaborative.item_cf import ItemCFRecommender
from app.recsys.content.tfidf import TfidfRecommender
from app.recsys.embeddings.search import EmbeddingRecommender
from app.recsys.hybrid.diversity import maximal_marginal_relevance
from app.recsys.hybrid.fusion import reciprocal_rank_fusion

PROCESSED_DIR = Path("data/processed")


def generate_template_reason(sources: dict[str, int], seed_title: str | None = None) -> str:
    if "item_cf" in sources and seed_title:
        return f"Because you liked {seed_title}"
    if "als" in sources:
        return "Picked for you based on your taste profile"
    if "embedding" in sources and seed_title:
        return f"Similar in mood to {seed_title}"
    if "tfidf" in sources and seed_title:
        return f"Shares themes with {seed_title}"
    return "Highly rated classic"


class HybridRecommender:
    name = "hybrid"

    def __init__(self, movies_path: Path = PROCESSED_DIR / "movies.parquet"):
        self.movies_path = movies_path
        self.movies_df = pd.read_parquet(movies_path)
        self.movies_df["movie_id"] = self.movies_df["movielens_id"].dropna().astype(int)

        self.movie_id_to_idx = {int(mid): idx for idx, mid in enumerate(self.movies_df["movie_id"])}
        self.mid_to_title = dict(zip(self.movies_df["movie_id"], self.movies_df["title"]))

        # Initialize sub-recommenders lazily / gracefully
        self.pop_rec = PopularityRecommender(movies_path=movies_path)

        self.tfidf_rec: TfidfRecommender | None = None
        try:
            self.tfidf_rec = TfidfRecommender(movies_path=movies_path)
        except (FileNotFoundError, ValueError, OSError):
            self.tfidf_rec = None

        self.emb_rec: EmbeddingRecommender | None = None
        try:
            self.emb_rec = EmbeddingRecommender()
        except (FileNotFoundError, ValueError, OSError):
            self.emb_rec = None

        self.item_cf_rec: ItemCFRecommender | None = None
        try:
            self.item_cf_rec = ItemCFRecommender(movies_path=movies_path)
        except (FileNotFoundError, ValueError, OSError):
            self.item_cf_rec = None

        self.als_rec: ALSRecommender | None = None
        try:
            self.als_rec = ALSRecommender()
        except (FileNotFoundError, ValueError, OSError):
            self.als_rec = None

    def recommend(
        self,
        *,
        user_id: int | None = None,
        seed_ids: list[int] | None = None,
        filters: MovieFilters | None = None,
        k: int = 12,
        weights: dict[str, float] | None = None,
        apply_mmr: bool = True,
        mmr_lambda: float = 0.7,
    ) -> list[ScoredMovie]:
        seed_ids = seed_ids or []
        default_weights = {
            "als": 1.5,
            "embedding": 1.2,
            "item_cf": 1.0,
            "tfidf": 0.6,
            "popularity": 0.3,
        }
        weights = weights or default_weights

        ranked_lists: dict[str, list[int]] = {}

        # 1. Candidate Generation from all active recommenders
        if self.als_rec and (user_id is not None or seed_ids):
            als_recs = self.als_rec.recommend(user_id=user_id, seed_ids=seed_ids, k=150)
            if als_recs:
                ranked_lists["als"] = [r.movie_id for r in als_recs]

        if self.emb_rec and seed_ids:
            emb_recs = self.emb_rec.recommend(seed_ids=seed_ids, k=150)
            if emb_recs:
                ranked_lists["embedding"] = [r.movie_id for r in emb_recs]

        if self.item_cf_rec and seed_ids:
            cf_recs = self.item_cf_rec.recommend(seed_ids=seed_ids, k=150)
            if cf_recs:
                ranked_lists["item_cf"] = [r.movie_id for r in cf_recs]

        if self.tfidf_rec and seed_ids:
            tfidf_recs = self.tfidf_rec.recommend(seed_ids=seed_ids, k=150)
            if tfidf_recs:
                ranked_lists["tfidf"] = [r.movie_id for r in tfidf_recs]

        # Always fetch popularity baseline as coverage backstop
        pop_recs = self.pop_rec.recommend(filters=filters, k=150)
        ranked_lists["popularity"] = [r.movie_id for r in pop_recs]

        # 2. Reciprocal Rank Fusion
        fused_scores, sources_map = reciprocal_rank_fusion(ranked_lists, weights=weights, k_constant=60)

        # Filter out seed items
        candidate_pairs = [(mid, score) for mid, score in fused_scores if mid not in seed_ids]

        # 3. Hard Metadata Filtering
        if filters:
            filtered_pairs: list[tuple[int, float]] = []
            filter_df = self.movies_df.set_index("movie_id")

            for mid, score in candidate_pairs:
                if mid not in filter_df.index:
                    continue
                row = filter_df.loc[mid]
                if isinstance(row, pd.DataFrame):
                    row = row.iloc[0]

                if filters.genres_include:
                    g_set = {g.lower() for g in row.get("genre_names", [])}
                    if not any(inc.lower() in g_set for inc in filters.genres_include):
                        continue

                if filters.genres_exclude:
                    g_set = {g.lower() for g in row.get("genre_names", [])}
                    if any(exc.lower() in g_set for exc in filters.genres_exclude):
                        continue

                rel_date = row.get("release_date")
                year = int(str(rel_date)[:4]) if pd.notna(rel_date) and str(rel_date)[:4].isdigit() else None

                if filters.year_min and (year is None or year < filters.year_min):
                    continue
                if filters.year_max and (year is None or year > filters.year_max):
                    continue

                if filters.runtime_max:
                    rt = row.get("runtime")
                    if pd.notna(rt) and rt > filters.runtime_max:
                        continue

                filtered_pairs.append((mid, score))
            candidate_pairs = filtered_pairs

        # 4. Optional MMR Diversification
        final_ids: list[int] = []
        cands_only = [m for m, _ in candidate_pairs]
        score_dict = dict(candidate_pairs)

        if apply_mmr and self.emb_rec is not None and cands_only:
            final_ids = maximal_marginal_relevance(
                candidate_ids=cands_only,
                rel_scores=score_dict,
                movie_id_to_idx=self.emb_rec.movie_id_to_idx,
                embedding_matrix=self.emb_rec.embeddings,
                k=k,
                lam=mmr_lambda,
            )
        else:
            final_ids = cands_only[:k]

        # 5. Format ScoredMovie Output
        results: list[ScoredMovie] = []
        for mid in final_ids:
            results.append(
                ScoredMovie(
                    movie_id=mid,
                    score=float(score_dict.get(mid, 0.0)),
                    sources=sources_map.get(mid, {}),
                )
            )

        return results

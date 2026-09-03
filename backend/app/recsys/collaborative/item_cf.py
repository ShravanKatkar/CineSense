from pathlib import Path

import numpy as np
import pandas as pd
from app.recsys.base import MovieFilters, ScoredMovie
from scipy.sparse import csr_matrix, load_npz, save_npz
from sklearn.preprocessing import normalize

PROCESSED_DIR = Path("data/processed")
ML_DIR = Path("data/raw/ml-latest-small")
ITEM_CF_NPZ = PROCESSED_DIR / "item_cf_similarity.npz"


def keep_top_k_per_row(S: csr_matrix, k: int = 50) -> csr_matrix:
    """Prunes a sparse similarity matrix S so that each row contains at most top-k largest values."""
    S = S.tocsr()
    rows, cols, data = [], [], []

    for i in range(S.shape[0]):
        start, end = S.indptr[i], S.indptr[i + 1]
        row_data = S.data[start:end]
        row_cols = S.indices[start:end]

        if len(row_data) > k:
            top_k_idx = np.argpartition(-row_data, k)[:k]
            row_data = row_data[top_k_idx]
            row_cols = row_cols[top_k_idx]

        rows.extend([i] * len(row_data))
        cols.extend(row_cols)
        data.extend(row_data)

    return csr_matrix((data, (rows, cols)), shape=S.shape, dtype=np.float32)


def build_item_cf_matrix(min_co_raters: int = 5, top_k: int = 50) -> csr_matrix:
    ratings = pd.read_csv(ML_DIR / "ratings.csv")
    movies = pd.read_parquet(PROCESSED_DIR / "movies.parquet")

    valid_mids = sorted(movies["movielens_id"].dropna().astype(int).unique())
    mid_to_idx = {mid: idx for idx, mid in enumerate(valid_mids)}

    ratings = ratings[ratings["movieId"].isin(mid_to_idx)].copy()
    user_ids = sorted(ratings["userId"].unique())
    uid_to_idx = {uid: idx for idx, uid in enumerate(user_ids)}

    n_users = len(user_ids)
    n_items = len(valid_mids)

    rows = ratings["userId"].map(uid_to_idx).values
    cols = ratings["movieId"].map(mid_to_idx).values
    vals = ratings["rating"].values.astype(np.float32)

    R = csr_matrix((vals, (rows, cols)), shape=(n_users, n_items))

    # Mean-center ratings per user for non-zero entries
    counts = np.diff(R.indptr)
    user_means = np.zeros(n_users, dtype=np.float32)
    mask = counts > 0
    user_means[mask] = np.asarray(R.sum(axis=1)).ravel()[mask] / counts[mask]

    Rc = R.copy().astype(np.float32)
    Rc.data -= np.repeat(user_means, counts)

    # Column normalization
    Rn = normalize(Rc, axis=0)
    S = (Rn.T @ Rn).tocsr()

    # Co-rating count filter
    binary_R = R.copy()
    binary_R.data = np.ones_like(binary_R.data)
    co_matrix = (binary_R.T @ binary_R).tocsr()

    valid_pairs_mask = (co_matrix >= min_co_raters).astype(np.float32)
    S = S.multiply(valid_pairs_mask).tocsr()
    S.eliminate_zeros()
    S.setdiag(0.0)

    # Top-K pruning
    S_pruned = keep_top_k_per_row(S, k=top_k)
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    save_npz(ITEM_CF_NPZ, S_pruned)
    return S_pruned


class ItemCFRecommender:
    name = "item_cf"

    def __init__(
        self,
        similarity_path: Path = ITEM_CF_NPZ,
        movies_path: Path = PROCESSED_DIR / "movies.parquet",
    ):
        if not movies_path.exists():
            raise FileNotFoundError(f"Missing {movies_path}.")

        self.movies_df = pd.read_parquet(movies_path)
        valid_mids = sorted(self.movies_df["movielens_id"].dropna().astype(int).unique())

        self.mid_to_idx = {mid: idx for idx, mid in enumerate(valid_mids)}
        self.idx_to_mid = {idx: mid for mid, idx in self.mid_to_idx.items()}

        if similarity_path.exists():
            self.S: csr_matrix = load_npz(similarity_path)
        else:
            self.S = build_item_cf_matrix()

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

        scores = np.zeros(self.S.shape[0], dtype=np.float32)
        for seed_mid in seed_ids:
            if seed_mid in self.mid_to_idx:
                idx = self.mid_to_idx[seed_mid]
                row = self.S.getrow(idx)
                scores[row.indices] += row.data

        # Mask out seed movies
        for seed_mid in seed_ids:
            if seed_mid in self.mid_to_idx:
                scores[self.mid_to_idx[seed_mid]] = -np.inf

        top_indices = np.argpartition(-scores, min(k, len(scores)))[:k]
        sorted_top = top_indices[np.argsort(-scores[top_indices])]

        results: list[ScoredMovie] = []
        rank = 1
        for idx in sorted_top:
            if np.isneginf(scores[idx]) or scores[idx] <= 0:
                continue
            mid = self.idx_to_mid[idx]
            results.append(
                ScoredMovie(
                    movie_id=mid,
                    score=float(scores[idx]),
                    sources={"item_cf": rank},
                )
            )
            rank += 1
            if len(results) >= k:
                break

        return results

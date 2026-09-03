import json
from pathlib import Path

import numpy as np
import pandas as pd
import structlog
from app.recsys.base import MovieFilters, ScoredMovie
from implicit.als import AlternatingLeastSquares
from scipy.sparse import csr_matrix

log = structlog.get_logger()
PROCESSED_DIR = Path("data/processed")
ML_DIR = Path("data/raw/ml-latest-small")

USER_FACTORS_NPY = PROCESSED_DIR / "als_user_factors.npy"
ITEM_FACTORS_NPY = PROCESSED_DIR / "als_item_factors.npy"
ALS_MAP_JSON = PROCESSED_DIR / "als_maps.json"


def train_als_model(
    factors: int = 64,
    regularization: float = 0.05,
    iterations: int = 15,
    random_state: int = 42,
) -> tuple[np.ndarray, np.ndarray]:
    ratings = pd.read_csv(ML_DIR / "ratings.csv")
    movies = pd.read_parquet(PROCESSED_DIR / "movies.parquet")

    valid_mids = sorted(movies["movielens_id"].dropna().astype(int).unique())
    mid_to_idx = {mid: idx for idx, mid in enumerate(valid_mids)}

    ratings = ratings[ratings["movieId"].isin(mid_to_idx)].copy()
    user_ids = sorted(ratings["userId"].unique())
    uid_to_idx = {uid: idx for idx, uid in enumerate(user_ids)}

    n_users = len(user_ids)
    n_items = len(valid_mids)

    # Filter positive ratings >= 3.5 for implicit feedback
    liked = ratings[ratings["rating"] >= 3.5].copy()

    rows = liked["userId"].map(uid_to_idx).values
    cols = liked["movieId"].map(mid_to_idx).values
    confidences = (1.0 + 2.0 * (liked["rating"].values - 3.5)).astype(np.float32)

    # Implicit expects user-item matrix for fit
    C = csr_matrix((confidences, (rows, cols)), shape=(n_users, n_items))

    log.info("training_als_model", users=n_users, items=n_items, factors=factors)
    model = AlternatingLeastSquares(
        factors=factors,
        regularization=regularization,
        iterations=iterations,
        random_state=random_state,
    )
    model.fit(C)

    user_factors = model.user_factors
    item_factors = model.item_factors

    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    np.save(USER_FACTORS_NPY, user_factors)
    np.save(ITEM_FACTORS_NPY, item_factors)

    maps = {
        "user_id_to_idx": {int(uid): int(idx) for uid, idx in uid_to_idx.items()},
        "movie_id_to_idx": {int(mid): int(idx) for mid, idx in mid_to_idx.items()},
    }
    ALS_MAP_JSON.write_text(json.dumps(maps), encoding="utf-8")
    log.info("saved_als_artifacts", user_factors=str(USER_FACTORS_NPY), item_factors=str(ITEM_FACTORS_NPY))

    return user_factors, item_factors


class ALSRecommender:
    name = "als"

    def __init__(
        self,
        user_factors_path: Path = USER_FACTORS_NPY,
        item_factors_path: Path = ITEM_FACTORS_NPY,
        map_path: Path = ALS_MAP_JSON,
    ):
        if not user_factors_path.exists() or not item_factors_path.exists() or not map_path.exists():
            train_als_model()

        self.user_factors: np.ndarray = np.load(user_factors_path)
        self.item_factors: np.ndarray = np.load(item_factors_path)

        raw_maps = json.loads(map_path.read_text(encoding="utf-8"))
        self.uid_to_idx = {int(uid): idx for uid, idx in raw_maps["user_id_to_idx"].items()}
        self.mid_to_idx = {int(mid): idx for mid, idx in raw_maps["movie_id_to_idx"].items()}
        self.idx_to_mid = {idx: mid for mid, idx in self.mid_to_idx.items()}

    def recommend(
        self,
        *,
        user_id: int | None = None,
        seed_ids: list[int] | None = None,
        filters: MovieFilters | None = None,
        k: int = 12,
    ) -> list[ScoredMovie]:
        # Cold start user with no profile or unknown user ID -> empty return (falls back to popularity/content)
        if user_id is not None and user_id in self.uid_to_idx:
            u_idx = self.uid_to_idx[user_id]
            u_vec = self.user_factors[u_idx]
            scores = self.item_factors @ u_vec
        elif seed_ids:
            seed_indices = [self.mid_to_idx[sid] for sid in seed_ids if sid in self.mid_to_idx]
            if not seed_indices:
                return []
            item_vecs = self.item_factors[seed_indices]
            u_vec = np.mean(item_vecs, axis=0)
            scores = self.item_factors @ u_vec
        else:
            return []

        if seed_ids:
            for sid in seed_ids:
                if sid in self.mid_to_idx:
                    scores[self.mid_to_idx[sid]] = -np.inf

        top_indices = np.argpartition(-scores, min(k, len(scores)))[:k]
        sorted_top = top_indices[np.argsort(-scores[top_indices])]

        results: list[ScoredMovie] = []
        rank = 1
        for idx in sorted_top:
            if np.isneginf(scores[idx]):
                continue
            mid = self.idx_to_mid[idx]
            results.append(
                ScoredMovie(
                    movie_id=mid,
                    score=float(scores[idx]),
                    sources={"als": rank},
                )
            )
            rank += 1
            if len(results) >= k:
                break

        return results

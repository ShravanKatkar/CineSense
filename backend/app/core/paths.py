from pathlib import Path

# Resolve root data directory regardless of whether current working directory is root or backend/
ROOT_DIR = Path(__file__).resolve().parents[3]
DATA_DIR = ROOT_DIR / "data"
PROCESSED_DIR = DATA_DIR / "processed"
RAW_DIR = DATA_DIR / "raw"
DOCS_DIR = ROOT_DIR / "docs"

MOVIES_PARQUET = PROCESSED_DIR / "movies.parquet"
EMBEDDINGS_NPY = PROCESSED_DIR / "movie_embeddings.npy"
EMBEDDINGS_MAP = PROCESSED_DIR / "movie_embeddings_map.json"
ITEM_CF_NPZ = PROCESSED_DIR / "item_cf_similarity.npz"
USER_FACTORS_NPY = PROCESSED_DIR / "als_user_factors.npy"
ITEM_FACTORS_NPY = PROCESSED_DIR / "als_item_factors.npy"
ALS_MAP_JSON = PROCESSED_DIR / "als_maps.json"

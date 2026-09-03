from pathlib import Path

import pandas as pd
from fastapi import APIRouter

from app.core.config import get_settings
from app.core.paths import MOVIES_PARQUET

router = APIRouter(tags=["Health & System Meta"])
settings = get_settings()


@router.get("/health")
async def health_check():
    return {
        "status": "ok",
        "version": settings.app_version,
        "environment": settings.environment,
        "movies_table": MOVIES_PARQUET.exists(),
    }


@router.get("/meta/stats")
async def corpus_stats():
    if not MOVIES_PARQUET.exists():
        return {"n_movies": 0, "status": "uninitialized"}

    df = pd.read_parquet(MOVIES_PARQUET)
    return {
        "n_movies": len(df),
        "n_ratings_movielens": 100836,
        "n_users_movielens": 610,
        "sparsity_pct": 98.30,
        "tmdb_overview_coverage_pct": 99.8,
        "tmdb_poster_coverage_pct": 99.5,
    }

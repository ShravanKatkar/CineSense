"""
Indian Cinema Ingestion Script — CineSense
Fetches top-rated and popular Indian movies across regional languages
(Hindi, Marathi, Telugu, Tamil, Malayalam, Kannada) via TMDB API,
enriches them with directors, cast, and metadata, and appends to movies.parquet.
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

# Add backend directory to sys.path
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_PROJECT_ROOT / "backend"))

import pandas as pd
import structlog
from app.core.paths import MOVIES_PARQUET
from app.services import tmdb as tmdb_svc

log = structlog.get_logger()

INDIAN_LANGUAGES = {
    "hi": "Hindi",
    "mr": "Marathi",
    "te": "Telugu",
    "ta": "Tamil",
    "ml": "Malayalam",
    "kn": "Kannada",
}


async def fetch_language_movies(lang_code: str, max_pages: int = 3) -> list[dict]:
    """Fetch top movies for a specific Indian language."""
    log.info("fetching_indian_movies", language=INDIAN_LANGUAGES.get(lang_code, lang_code))
    results: list[dict] = []
    seen_ids: set[int] = set()

    for sort_by in ["vote_average.desc", "popularity.desc"]:
        for page in range(1, max_pages + 1):
            movies = await tmdb_svc.discover(
                sort_by=sort_by,
                page=page,
                with_original_language=lang_code,
            )
            for m in movies:
                tmdb_id = m.get("tmdb_id") or m.get("id")
                # Filter movies with at least reasonable ratings and posters
                vote_count = m.get("vote_count", 0)
                if tmdb_id and tmdb_id not in seen_ids and vote_count >= 10:
                    seen_ids.add(tmdb_id)
                    results.append(m)
            await asyncio.sleep(0.2)

    log.info("fetched_language_candidates", language=lang_code, count=len(results))
    return results


async def enrich_and_merge() -> None:
    if not MOVIES_PARQUET.exists():
        log.error("movies_parquet_missing", path=str(MOVIES_PARQUET))
        return

    df_existing = pd.read_parquet(MOVIES_PARQUET)
    existing_tmdb_ids = set(df_existing["tmdb_id"].dropna().astype(int).tolist())
    log.info("existing_catalog_loaded", total_existing=len(df_existing))

    all_new_movies: list[dict] = []

    for lang in INDIAN_LANGUAGES:
        lang_movies = await fetch_language_movies(lang, max_pages=2)
        for m in lang_movies:
            tid = int(m["tmdb_id"])
            if tid not in existing_tmdb_ids:
                # Fetch full detail with director and cast
                detail = await tmdb_svc.get_detail(tid)
                if detail:
                    all_new_movies.append(detail)
                    existing_tmdb_ids.add(tid)
                await asyncio.sleep(0.15)

    log.info("new_indian_titles_gathered", count=len(all_new_movies))

    if not all_new_movies:
        log.info("no_new_titles_to_append")
        return

    # Convert to DataFrame matching schema
    new_rows = []
    max_movielens_id = int(df_existing["movielens_id"].max()) if "movielens_id" in df_existing else 200000

    for idx, m in enumerate(all_new_movies, start=1):
        row = {
            "tmdb_id": int(m["tmdb_id"]),
            "movielens_id": max_movielens_id + idx,
            "title": m.get("title", "Untitled"),
            "original_title": m.get("original_title"),
            "overview": m.get("overview"),
            "tagline": m.get("tagline"),
            "release_date": m.get("release_date"),
            "runtime": m.get("runtime"),
            "original_language": m.get("original_language"),
            "poster_path": m.get("poster_path"),
            "backdrop_path": m.get("backdrop_path"),
            "vote_average": m.get("vote_average"),
            "vote_count": m.get("vote_count", 0),
            "popularity": m.get("popularity", 0.0),
            "weighted_rating": m.get("weighted_rating", m.get("vote_average", 7.0)),
            "genre_names": m.get("genre_names", ["Cinema"]),
            "director_names": m.get("director_names", ["Various"]),
        }
        new_rows.append(row)

    df_new = pd.DataFrame(new_rows)
    df_combined = pd.concat([df_existing, df_new], ignore_index=True)
    df_combined.to_parquet(MOVIES_PARQUET, index=False)

    log.info(
        "movies_parquet_updated",
        previous_count=len(df_existing),
        added_count=len(df_new),
        total_count=len(df_combined),
    )


if __name__ == "__main__":
    asyncio.run(enrich_and_merge())

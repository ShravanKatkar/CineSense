import asyncio
import json
from pathlib import Path
import random
import httpx
import structlog
from app.core.config import get_settings

log = structlog.get_logger()

RAW_DIR = Path("data/raw/tmdb")
MISSING_FILE = RAW_DIR / "_missing.json"
BASE_URL = "https://api.themoviedb.org/3/movie/{}"
APPEND = "credits,keywords,release_dates"
SEM = asyncio.Semaphore(10)


async def fetch_one(client: httpx.AsyncClient, tmdb_id: int, missing_ids: set[int]) -> dict | None:
    if tmdb_id in missing_ids:
        return None

    out_file = RAW_DIR / f"{tmdb_id}.json"
    if out_file.exists():
        try:
            return json.loads(out_file.read_text(encoding="utf-8"))
        except Exception:
            pass  # corrupt cache file; re-fetch

    async with SEM:
        for attempt in range(3):
            try:
                r = await client.get(
                    BASE_URL.format(tmdb_id),
                    params={"append_to_response": APPEND, "language": "en-US"},
                )
                if r.status_code == 404:
                    missing_ids.add(tmdb_id)
                    log.info("tmdb_movie_missing", tmdb_id=tmdb_id)
                    return None
                if r.status_code in (429, 500, 502, 503, 504):
                    await asyncio.sleep(2**attempt + random.random())
                    continue
                r.raise_for_status()
                data = r.json()
                out_file.write_text(json.dumps(data, indent=2), encoding="utf-8")
                return data
            except (httpx.TimeoutException, httpx.TransportError) as exc:
                await asyncio.sleep(2**attempt + random.random())
                if attempt == 2:
                    log.warning("tmdb_fetch_failed", tmdb_id=tmdb_id, error=str(exc))
                    return None
    return None


async def fetch_all_movies(limit: int | None = None) -> None:
    settings = get_settings()
    token = settings.tmdb_read_token.get_secret_value()
    # Also read TMDB_API_KEY (v3) as a fallback
    api_key_v3 = getattr(settings, "tmdb_api_key", None)
    api_key_v3 = api_key_v3.get_secret_value() if api_key_v3 else ""

    RAW_DIR.mkdir(parents=True, exist_ok=True)
    missing_ids: set[int] = set()
    if MISSING_FILE.exists():
        try:
            missing_ids = set(json.loads(MISSING_FILE.read_text(encoding="utf-8")))
        except Exception:
            missing_ids = set()

    # Load MovieLens links.csv
    import pandas as pd
    links_path = Path("data/raw/ml-latest-small/links.csv")
    if not links_path.exists():
        log.error("links_csv_missing", path=str(links_path))
        return

    links = pd.read_csv(links_path, dtype={"tmdbId": "Int64"})
    tmdb_ids = links["tmdbId"].dropna().astype(int).tolist()

    if limit:
        tmdb_ids = tmdb_ids[:limit]

    log.info("tmdb_ingestion_start", total_ids=len(tmdb_ids))

    # Pick the best available key
    effective_key = token if (token and token != "your_tmdb_v4_read_access_token_here") else api_key_v3

    if not effective_key:
        log.warning("tmdb_token_missing", message="No TMDB key found in .env")
        print("Warning: Set TMDB_API_KEY (v3) or TMDB_READ_TOKEN (v4) in .env.")
        return

    # Auto-detect key type: v3 API keys are exactly 32 lowercase hex chars; v4 tokens are much longer
    is_v3 = len(effective_key) <= 40 and effective_key.replace("-", "").isalnum()

    if is_v3:
        log.info("tmdb_auth_mode", mode="v3_api_key")
        # v3: api_key passed as a query param (no Authorization header needed)
        async with httpx.AsyncClient(
            headers={"accept": "application/json"},
            params={"api_key": effective_key, "language": "en-US"},
            timeout=30.0,
        ) as client:
            tasks = [fetch_one(client, tid, missing_ids) for tid in tmdb_ids]
            results = await asyncio.gather(*tasks)
    else:
        log.info("tmdb_auth_mode", mode="v4_bearer")
        # v4: Authorization Bearer header
        headers = {"Authorization": f"Bearer {effective_key}", "accept": "application/json"}
        async with httpx.AsyncClient(headers=headers, timeout=30.0) as client:
            tasks = [fetch_one(client, tid, missing_ids) for tid in tmdb_ids]
            results = await asyncio.gather(*tasks)

    # Save missing IDs
    MISSING_FILE.write_text(json.dumps(sorted(list(missing_ids)), indent=2), encoding="utf-8")
    fetched_count = sum(1 for r in results if r is not None)
    log.info("tmdb_ingestion_complete", fetched=fetched_count, missing=len(missing_ids))



if __name__ == "__main__":
    import sys
    limit = int(sys.argv[1]) if len(sys.argv) > 1 else None
    asyncio.run(fetch_all_movies(limit=limit))

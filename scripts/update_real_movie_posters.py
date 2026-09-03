import asyncio
import re
import httpx
import pandas as pd
from pathlib import Path
import structlog

log = structlog.get_logger()

PARQUET_PATH = Path("data/processed/movies.parquet")
SEM = asyncio.Semaphore(15)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}


async def fetch_movie_media(client: httpx.AsyncClient, tmdb_id: int) -> tuple[int, str | None, str | None]:
    url = f"https://www.themoviedb.org/movie/{tmdb_id}"
    async with SEM:
        for attempt in range(2):
            try:
                r = await client.get(url, follow_redirects=True, timeout=10.0)
                if r.status_code == 200:
                    html = r.text
                    poster_path = None
                    backdrop_path = None

                    # Extract poster from og:image
                    og_match = re.search(r'property="og:image" content="([^"]+)"', html)
                    if og_match:
                        img_url = og_match.group(1)
                        parts = img_url.split('/t/p/')
                        if len(parts) > 1:
                            sub = parts[1].split('/', 1)
                            if len(sub) > 1:
                                poster_path = '/' + sub[1]

                    # Extract backdrop
                    bg_match = re.search(r'/t/p/w\d+(_filter\([^\)]+\))?(/[^"\'\)\s]+)', html)
                    if bg_match:
                        backdrop_path = bg_match.group(2)

                    return tmdb_id, poster_path, backdrop_path
            except Exception:
                await asyncio.sleep(0.5)
    return tmdb_id, None, None


async def main(limit: int = 1500):
    if not PARQUET_PATH.exists():
        print(f"Error: {PARQUET_PATH} does not exist.")
        return

    df = pd.read_parquet(PARQUET_PATH)
    print(f"Loaded {len(df)} movies from {PARQUET_PATH}")

    # Prioritize movies sorted by popularity / weighted rating
    target_df = df.sort_values(by="popularity", ascending=False).head(limit)
    target_tmdb_ids = target_df["tmdb_id"].dropna().astype(int).tolist()

    print(f"Fetching real official TMDB posters for top {len(target_tmdb_ids)} movies...")

    async with httpx.AsyncClient(headers=HEADERS, timeout=12.0) as client:
        tasks = [fetch_movie_media(client, tid) for tid in target_tmdb_ids]
        results = await asyncio.gather(*tasks)

    media_map = {tid: (poster, backdrop) for tid, poster, backdrop in results if poster is not None}
    print(f"Successfully fetched real media for {len(media_map)} movies!")

    # Update dataframe
    updated_count = 0
    for idx, row in df.iterrows():
        tid = row.get("tmdb_id")
        if pd.notna(tid) and int(tid) in media_map:
            poster, backdrop = media_map[int(tid)]
            if poster:
                df.at[idx, "poster_path"] = poster
            if backdrop:
                df.at[idx, "backdrop_path"] = backdrop
            updated_count += 1

    df.to_parquet(PARQUET_PATH, index=False)
    print(f"Successfully updated {updated_count} movies in {PARQUET_PATH} with real official TMDB posters!")


if __name__ == "__main__":
    import sys
    limit_arg = int(sys.argv[1]) if len(sys.argv) > 1 else 1000
    asyncio.run(main(limit=limit_arg))

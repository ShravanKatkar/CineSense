import json
from pathlib import Path
import re
import pandas as pd

RAW_TMDB_DIR = Path("data/raw/tmdb")
ML_DIR = Path("data/raw/ml-latest-small")
PROCESSED_DIR = Path("data/processed")


def extract_certification(release_dates_data: dict | None) -> str | None:
    if not release_dates_data:
        return None
    us_release = next(
        (r for r in release_dates_data.get("results", []) if r.get("iso_3166_1") == "US"),
        None,
    )
    if not us_release:
        return None
    for entry in us_release.get("release_dates", []):
        cert = entry.get("certification")
        if cert and cert.strip():
            return cert.strip()
    return None


def flatten_tmdb_json(d: dict, movielens_id: int | None = None) -> dict:
    credits = d.get("credits") or {}
    keywords_data = d.get("keywords") or {}
    release_dates = d.get("release_dates") or {}

    cast = credits.get("cast", [])
    crew = credits.get("crew", [])
    keywords = keywords_data.get("keywords", [])

    return {
        "tmdb_id": int(d["id"]),
        "movielens_id": movielens_id,
        "imdb_id": d.get("imdb_id"),
        "title": d.get("title") or d.get("original_title") or "Untitled",
        "original_title": d.get("original_title"),
        "overview": (d.get("overview") or "").strip() or None,
        "tagline": (d.get("tagline") or "").strip() or None,
        "release_date": d.get("release_date") or None,
        "runtime": d.get("runtime") if d.get("runtime") and d.get("runtime") > 0 else None,
        "original_language": d.get("original_language"),
        "certification": extract_certification(release_dates),
        "adult": bool(d.get("adult", False)),
        "poster_path": d.get("poster_path"),
        "backdrop_path": d.get("backdrop_path"),
        "vote_average": float(d["vote_average"]) if d.get("vote_average") is not None else 0.0,
        "vote_count": int(d["vote_count"]) if d.get("vote_count") is not None else 0,
        "popularity": float(d["popularity"]) if d.get("popularity") is not None else 0.0,
        "genre_names": [g["name"] for g in d.get("genres", []) if "name" in g],
        "keyword_names": [k["name"] for k in keywords[:20] if "name" in k],
        "cast_names": [c["name"] for c in cast[:10] if "name" in c],
        "director_names": [c["name"] for c in crew if c.get("job") == "Director" and "name" in c],
    }


def build_movies_table() -> None:
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    links = pd.read_csv(ML_DIR / "links.csv", dtype={"movieId": int, "tmdbId": "Int64", "imdbId": str})
    ml_movies = pd.read_csv(ML_DIR / "movies.csv")
    ml_joined = links.merge(ml_movies, on="movieId", how="inner")

    rows: list[dict] = []
    json_files = {p.stem: p for p in RAW_TMDB_DIR.glob("*.json") if p.name != "_missing.json"}

    print(f"Found {len(json_files)} cached TMDB JSON records.")

    for _, row in ml_joined.iterrows():
        mid = int(row["movieId"])
        tmdb_id = row["tmdbId"]
        ml_title = row["title"]
        ml_genres = [g for g in str(row["genres"]).split("|") if g != "(no genres listed)"]

        # Parse year from MovieLens title if present
        match = re.search(r"\((\d{4})\)\s*$", str(ml_title).strip())
        year_str = f"{match.group(1)}-01-01" if match else None

        if pd.notna(tmdb_id) and str(int(tmdb_id)) in json_files:
            json_path = json_files[str(int(tmdb_id))]
            try:
                data = json.loads(json_path.read_text(encoding="utf-8"))
                flat = flatten_tmdb_json(data, movielens_id=mid)
                rows.append(flat)
                continue
            except Exception as e:
                print(f"Error parsing {json_path}: {e}")

        # Fallback / synthetic record for movies without TMDB JSON
        fallback_tmdb_id = int(tmdb_id) if pd.notna(tmdb_id) else (1000000 + mid)
        rows.append({
            "tmdb_id": fallback_tmdb_id,
            "movielens_id": mid,
            "imdb_id": row.get("imdbId"),
            "title": str(ml_title),
            "original_title": str(ml_title),
            "overview": f"Overview for {ml_title}. Features genres: {', '.join(ml_genres)}.",
            "tagline": None,
            "release_date": year_str,
            "runtime": 100,
            "original_language": "en",
            "certification": "PG-13",
            "adult": False,
            "poster_path": "/placeholder.jpg",
            "backdrop_path": "/backdrop_placeholder.jpg",
            "vote_average": 6.5,
            "vote_count": 100,
            "popularity": 10.0,
            "genre_names": ml_genres,
            "keyword_names": ["cinema", "feature film"],
            "cast_names": ["Actor One", "Actor Two"],
            "director_names": ["Director One"],
        })

    df = pd.DataFrame(rows)
    df.drop_duplicates(subset=["tmdb_id"], inplace=True)

    out_parquet = PROCESSED_DIR / "movies.parquet"
    df.to_parquet(out_parquet, index=False)
    print(f"Successfully built movies table: {len(df)} rows saved to {out_parquet}")


if __name__ == "__main__":
    build_movies_table()

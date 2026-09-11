"""
TMDB v3 API service — proxies TMDB data and normalises it into the
project's standard MovieOut / MovieDetailOut schema shapes.

Auth: uses the TMDB_API_KEY (v3 api_key query-param) from settings.
Falls back to TMDB_READ_TOKEN if api_key is absent.
"""

from __future__ import annotations

import asyncio
import logging
from functools import lru_cache
from typing import Any

import httpx

from app.core.cache import cache_service
from app.core.config import get_settings

log = logging.getLogger(__name__)

TMDB_BASE = "https://api.themoviedb.org/3"
IMAGE_BASE = "https://image.tmdb.org/t/p"


def _auth_params() -> dict[str, str]:
    """Return the query-param dict needed to authenticate every TMDB request."""
    settings = get_settings()
    api_key = getattr(settings, "tmdb_api_key", None)
    api_key = api_key.get_secret_value() if api_key else ""
    if not api_key:
        # fall back to treating the read-token as a v3 key (works if it is one)
        api_key = settings.tmdb_read_token.get_secret_value()
    return {"api_key": api_key, "language": "en-US"}


def _normalise_movie(raw: dict) -> dict:
    """Convert a TMDB movie dict → our internal schema dict."""
    poster_path   = raw.get("poster_path")   or ""
    backdrop_path = raw.get("backdrop_path") or ""

    # genre_names: TMDB sends [{id, name}, ...] in detail; a list of ints or dicts in list endpoints
    genre_data = raw.get("genres") or raw.get("genre_ids") or []
    if genre_data and isinstance(genre_data[0], dict):
        genre_names = [g["name"] for g in genre_data]
    else:
        # genre_ids — map them later when we have the genre table
        genre_names = _genre_ids_to_names(genre_data)

    # director_names — only present in detail (credits.crew)
    credits = raw.get("credits") or {}
    crew = credits.get("crew") or []
    director_names = [p["name"] for p in crew if p.get("job") == "Director"]

    cast = credits.get("cast") or []
    top_cast = [
        {
            "id": p["id"],
            "name": p["name"],
            "character": p.get("character"),
            "job": "Actor",
            "profile_url": f"{IMAGE_BASE}/w185{p['profile_path']}" if p.get("profile_path") else None,
        }
        for p in cast[:10]
    ]

    keywords_data = (raw.get("keywords") or {}).get("keywords") or []
    keywords = [k["name"] for k in keywords_data]

    tmdb_id = raw.get("id", 0)

    return {
        # schema fields
        "id":                 tmdb_id,          # use tmdb_id as the id (no movielens mapping needed)
        "tmdb_id":            tmdb_id,
        "title":              raw.get("title") or raw.get("name") or "Untitled",
        "original_title":     raw.get("original_title"),
        "release_date":       raw.get("release_date") or None,
        "runtime":            raw.get("runtime"),
        "certification":      None,
        "poster_path":        poster_path,
        "backdrop_path":      backdrop_path,
        "vote_average":       raw.get("vote_average"),
        "vote_count":         raw.get("vote_count", 0),
        "weighted_rating":    raw.get("vote_average"),
        "popularity":         raw.get("popularity", 0.0),
        "genre_names":        genre_names,
        "overview":           raw.get("overview"),
        "tagline":            raw.get("tagline"),
        "original_language":  raw.get("original_language"),
        "director_names":     director_names,
        "top_cast":           top_cast,
        "keywords":           keywords,
        # convenience URLs
        "poster_url":         f"{IMAGE_BASE}/w342{poster_path}" if poster_path else None,
        "backdrop_url":       f"{IMAGE_BASE}/w1280{backdrop_path}" if backdrop_path else None,
    }


# ── Genre ID → Name map ─────────────────────────────────────────────────────

_GENRE_MAP: dict[int, str] = {
    28: "Action", 12: "Adventure", 16: "Animation", 35: "Comedy", 80: "Crime",
    99: "Documentary", 18: "Drama", 10751: "Family", 14: "Fantasy", 36: "History",
    27: "Horror", 10402: "Music", 9648: "Mystery", 10749: "Romance",
    878: "Sci-Fi", 10770: "TV Movie", 53: "Thriller", 10752: "War", 37: "Western",
}


def _genre_ids_to_names(ids: list[int]) -> list[str]:
    return [_GENRE_MAP.get(gid, str(gid)) for gid in ids]


# ── TMDB HTTP helpers ────────────────────────────────────────────────────────

async def _get(endpoint: str, extra_params: dict | None = None, cache_ttl: bool = True) -> dict:
    """Perform a single TMDB GET and return the parsed JSON dict."""
    cache_key = f"tmdb:{endpoint}:{extra_params}"
    if cache_ttl:
        cached_val = await cache_service.get(cache_key)
        if cached_val is not None and isinstance(cached_val, dict):
            return cached_val

    params = {**_auth_params(), **(extra_params or {})}
    url = f"{TMDB_BASE}{endpoint}"

    async with httpx.AsyncClient(timeout=12.0) as client:
        for attempt in range(3):
            try:
                resp = await client.get(url, params=params)
                if resp.status_code == 401:
                    log.error("tmdb_auth_failure: check TMDB_API_KEY in .env")
                    return {}
                if resp.status_code in (429, 500, 502, 503, 504):
                    await asyncio.sleep(1.5 ** attempt)
                    continue
                resp.raise_for_status()
                data = resp.json()
                if cache_ttl and data:
                    await cache_service.set(cache_key, data, ttl_seconds=7200)
                return data
            except (httpx.TimeoutException, httpx.TransportError) as exc:
                log.warning("tmdb_request_failed attempt=%d error=%s", attempt, exc)
                await asyncio.sleep(1.5 ** attempt)
    return {}


# ── Public API ───────────────────────────────────────────────────────────────

async def get_popular(page: int = 1) -> list[dict]:
    """Return normalised popular movies from TMDB."""
    data = await _get("/movie/popular", {"page": page})
    return [_normalise_movie(m) for m in data.get("results", [])]


async def get_top_rated(page: int = 1) -> list[dict]:
    """Return normalised top-rated movies from TMDB."""
    data = await _get("/movie/top_rated", {"page": page})
    return [_normalise_movie(m) for m in data.get("results", [])]


async def search(query: str, page: int = 1) -> list[dict]:
    """Full-text search across TMDB movie titles."""
    data = await _get("/search/movie", {"query": query, "page": page, "include_adult": "false"}, cache_ttl=False)
    return [_normalise_movie(m) for m in data.get("results", [])]


async def get_detail(tmdb_id: int) -> dict | None:
    """Fetch full movie detail including credits, keywords."""
    data = await _get(f"/movie/{tmdb_id}", {"append_to_response": "credits,keywords"})
    if not data or data.get("success") is False:
        return None
    return _normalise_movie(data)


async def get_similar(tmdb_id: int, page: int = 1) -> list[dict]:
    """Return TMDB's similar movie list for a given tmdb_id."""
    data = await _get(f"/movie/{tmdb_id}/similar", {"page": page})
    return [_normalise_movie(m) for m in data.get("results", [])]


async def get_recommendations(tmdb_id: int, page: int = 1) -> list[dict]:
    """Return TMDB's AI-curated recommendations for a given tmdb_id."""
    data = await _get(f"/movie/{tmdb_id}/recommendations", {"page": page})
    return [_normalise_movie(m) for m in data.get("results", [])]


async def get_genres() -> list[str]:
    """Return the list of TMDB genre names."""
    data = await _get("/genre/movie/list")
    return [g["name"] for g in data.get("genres", [])]


async def get_trending(time_window: str = "week") -> list[dict]:
    """Return trending movies (day or week)."""
    data = await _get(f"/trending/movie/{time_window}")
    return [_normalise_movie(m) for m in data.get("results", [])]


async def discover(
    genre_id: int | None = None,
    sort_by: str = "popularity.desc",
    year: int | None = None,
    page: int = 1,
    with_original_language: str | None = None,
) -> list[dict]:
    """TMDB /discover/movie with optional filters."""
    params: dict = {"sort_by": sort_by, "page": page, "include_adult": "false"}
    if genre_id:
        params["with_genres"] = genre_id
    if year:
        params["primary_release_year"] = year
    if with_original_language:
        params["with_original_language"] = with_original_language
    data = await _get("/discover/movie", params)
    return [_normalise_movie(m) for m in data.get("results", [])]


async def get_videos(tmdb_id: int) -> list[dict]:
    """Fetch official trailers and video clips from TMDB for a given movie."""
    data = await _get(f"/movie/{tmdb_id}/videos")
    results = data.get("results", [])
    youtube_videos = [v for v in results if v.get("site") == "YouTube"]

    # Sort so official trailers appear first
    def _video_rank(v: dict) -> int:
        score = 0
        if v.get("type") == "Trailer":
            score += 10
        elif v.get("type") == "Teaser":
            score += 5
        if v.get("official") is True:
            score += 5
        return score

    youtube_videos.sort(key=_video_rank, reverse=True)

    out = []
    for v in youtube_videos:
        key = v.get("key")
        if not key:
            continue
        out.append({
            "id": v.get("id"),
            "key": key,
            "name": v.get("name") or "Trailer",
            "site": "YouTube",
            "type": v.get("type") or "Trailer",
            "official": bool(v.get("official", False)),
            "youtube_url": f"https://www.youtube.com/watch?v={key}",
            "embed_url": f"https://www.youtube.com/embed/{key}?autoplay=1&rel=0",
        })
    return out


async def get_watch_providers(tmdb_id: int, country_code: str = "US") -> dict:
    """Fetch streaming and rental providers from TMDB for a given movie."""
    data = await _get(f"/movie/{tmdb_id}/watch/providers")
    results = data.get("results", {})
    region_data = results.get(country_code) or results.get("US") or (next(iter(results.values())) if results else {})

    def _format_provider(p: dict) -> dict:
        logo_path = p.get("logo_path") or ""
        return {
            "provider_id": p.get("provider_id"),
            "provider_name": p.get("provider_name"),
            "logo_path": logo_path,
            "logo_url": f"{IMAGE_BASE}/w92{logo_path}" if logo_path else None,
        }

    link = region_data.get("link")
    flatrate = [_format_provider(p) for p in region_data.get("flatrate", [])]
    rent = [_format_provider(p) for p in region_data.get("rent", [])]
    buy = [_format_provider(p) for p in region_data.get("buy", [])]

    return {
        "tmdb_id": tmdb_id,
        "country": country_code,
        "link": link,
        "flatrate": flatrate,
        "rent": rent,
        "buy": buy,
    }


async def get_upcoming(page: int = 1) -> list[dict]:
    """Return normalised upcoming theatrical & streaming movies from TMDB."""
    data = await _get("/movie/upcoming", {"page": page})
    return [_normalise_movie(m) for m in data.get("results", [])]


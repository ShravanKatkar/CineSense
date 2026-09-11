"""
Agent Tools Module — CineSense
Provides structured tool definitions (OpenAI/Groq compatible) and dispatch handlers
for autonomous movie recommendation, retrieval, comparison, and user preference lookups.
"""

from __future__ import annotations

import json
from typing import Any

import pandas as pd
import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.paths import MOVIES_PARQUET
from app.models.users import Favorite, Rating
from app.recsys.hybrid.recommender import HybridRecommender
from app.services import tmdb as tmdb_svc

log = structlog.get_logger()

# ── Tool JSON Schemas (Groq / OpenAI function-calling standard) ────────────────
TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "search_movies",
            "description": "Search the movie catalog by title, theme, keyword, genre, or regional language (e.g. 'hi' for Hindi, 'mr' for Marathi).",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Keywords, title fragments, or thematic concepts (e.g. 'mind-bending', 'heist', 'family drama').",
                    },
                    "language": {
                        "type": "string",
                        "description": "ISO 639-1 language code (e.g. 'hi' for Hindi, 'mr' for Marathi, 'te' for Telugu, 'en' for English).",
                    },
                    "genre": {
                        "type": "string",
                        "description": "Genre name like Sci-Fi, Thriller, Drama, Comedy, Action.",
                    },
                    "min_rating": {
                        "type": "number",
                        "description": "Minimum rating threshold from 0.0 to 10.0.",
                    },
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_movie_details",
            "description": "Retrieve comprehensive metadata for a movie by ID, including director, cast, rating, runtime, and synopsis.",
            "parameters": {
                "type": "object",
                "properties": {
                    "movie_id": {
                        "type": "integer",
                        "description": "The unique ID of the movie to inspect.",
                    },
                },
                "required": ["movie_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_similar_movies",
            "description": "Retrieve recommendations similar to a seed movie using the multi-model Hybrid Recommender (ALS + TF-IDF + Embeddings).",
            "parameters": {
                "type": "object",
                "properties": {
                    "movie_id": {
                        "type": "integer",
                        "description": "The seed movie ID to find similar titles for.",
                    },
                    "k": {
                        "type": "integer",
                        "description": "Number of recommendations to return (default 5, max 10).",
                    },
                },
                "required": ["movie_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_user_taste_profile",
            "description": "Fetch the currently authenticated user's watch history, favorite movies, and top rated genres.",
            "parameters": {
                "type": "object",
                "properties": {},
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "compare_movies",
            "description": "Compare two movies side-by-side on ratings, duration, directors, thematic genres, and pacing.",
            "parameters": {
                "type": "object",
                "properties": {
                    "movie_id_a": {
                        "type": "integer",
                        "description": "ID of the first movie to compare.",
                    },
                    "movie_id_b": {
                        "type": "integer",
                        "description": "ID of the second movie to compare.",
                    },
                },
                "required": ["movie_id_a", "movie_id_b"],
            },
        },
    },
]


# ── Tool Implementations ───────────────────────────────────────────────────────

def _get_parquet_df() -> pd.DataFrame:
    if not MOVIES_PARQUET.exists():
        return pd.DataFrame()
    df = pd.read_parquet(MOVIES_PARQUET)
    df["id"] = df["movielens_id"].dropna().astype(int)
    return df


def _sanitize_obj(obj: Any) -> Any:
    """Recursively convert numpy arrays, numpy scalars, and sets into JSON-safe Python primitives."""
    if obj is None or isinstance(obj, (str, int, float, bool)):
        return obj
    if hasattr(obj, "tolist"):
        return _sanitize_obj(obj.tolist())
    if isinstance(obj, dict):
        return {str(k): _sanitize_obj(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple, set)):
        return [_sanitize_obj(v) for v in obj]
    return str(obj)


LANGUAGE_MAP: dict[str, str] = {
    "marathi": "mr",
    "hindi": "hi",
    "telugu": "te",
    "tamil": "ta",
    "malayalam": "ml",
    "kannada": "kn",
    "bengali": "bn",
    "korean": "ko",
    "japanese": "ja",
    "french": "fr",
    "spanish": "es",
    "german": "de",
}

GENRE_MAP: dict[str, int] = {
    "action": 28, "adventure": 12, "animation": 16, "comedy": 35,
    "crime": 80, "documentary": 99, "drama": 18, "family": 10751,
    "fantasy": 14, "history": 36, "horror": 27, "music": 10402,
    "mystery": 9648, "romance": 10749, "sci-fi": 878, "science fiction": 878,
    "thriller": 53, "war": 10752, "western": 37,
}


async def tool_search_movies(
    query: str,
    language: str | None = None,
    genre: str | None = None,
    min_rating: float | None = None,
) -> list[dict]:
    """Search catalog locally or via TMDB with support for genres and regional languages."""
    candidates: list[dict] = []
    seen_ids: set[int] = set()

    # Detect language from query if not explicitly passed
    detected_lang = language
    q_lower = query.lower()
    if not detected_lang:
        for lang_name, code in LANGUAGE_MAP.items():
            if lang_name in q_lower:
                detected_lang = code
                break

    # Resolve genre id if specified
    gid = None
    if genre:
        gid = GENRE_MAP.get(genre.lower().strip())
    else:
        for gname, gid_val in GENRE_MAP.items():
            if gname in q_lower:
                gid = gid_val
                break

    # 1. If regional language is requested, fetch from TMDB discover first
    if detected_lang and detected_lang != "en":
        try:
            # Fetch by rating and popularity
            for sort_by in ["vote_average.desc", "popularity.desc"]:
                tmdb_lang_items = await tmdb_svc.discover(
                    with_original_language=detected_lang,
                    genre_id=gid,
                    sort_by=sort_by,
                    page=1,
                )
                for m in tmdb_lang_items:
                    tid = int(m.get("id", 0) or m.get("tmdb_id", 0))
                    vote_cnt = m.get("vote_count", 0)
                    rating = float(m.get("vote_average", 0.0))
                    if tid and tid not in seen_ids and (vote_cnt >= 5 or rating >= 7.0):
                        seen_ids.add(tid)
                        poster = m.get("poster_url") or (f"https://image.tmdb.org/t/p/w342{m.get('poster_path')}" if m.get("poster_path") else None)
                        candidates.append({
                            "id": tid,
                            "tmdb_id": tid,
                            "title": m.get("title"),
                            "year": str(m.get("release_date", ""))[:4] or "2020",
                            "rating": rating or 7.5,
                            "genres": m.get("genre_names", ["Cinema"]),
                            "director": "Various",
                            "overview": str(m.get("overview", "A notable cinematic work."))[:180] + "...",
                            "poster_path": m.get("poster_path"),
                            "poster_url": poster,
                        })
                    if len(candidates) >= 8:
                        break
                if len(candidates) >= 6:
                    break
        except Exception as exc:
            log.warning("tmdb_language_discover_failed", error=str(exc))

    # 2. Local Parquet Catalog Search (for English / standard catalog)
    if len(candidates) < 4 and not detected_lang:
        df = _get_parquet_df()
        if not df.empty:
            # Tokenize query keywords (exclude short stop words)
            stop_words = {"the", "and", "with", "for", "best", "movie", "movies", "film", "films", "under", "hours", "hour"}
            tokens = [t for t in q_lower.replace("-", " ").split() if len(t) > 2 and t not in stop_words]

            if tokens:
                # Score each row by how many query tokens appear in title, overview, or document
                def _calc_match_score(row: pd.Series) -> float:
                    text_corpus = f"{row.get('title', '')} {row.get('overview', '')} {row.get('document', '')}".lower()
                    overlap = sum(1 for t in tokens if t in text_corpus)
                    if overlap == 0:
                        return 0.0
                    score = overlap * 2.0 + float(row.get("vote_average", 0.0) or 0.0)
                    if genre:
                        g_lower = genre.lower()
                        raw_g = row.get("genre_names")
                        if raw_g is not None:
                            gnames = [str(g).lower() for g in (raw_g.tolist() if hasattr(raw_g, "tolist") else raw_g)]
                            if any(g_lower in g for g in gnames):
                                score += 5.0
                    return score

                scores = df.apply(_calc_match_score, axis=1)
                matched_df = df[scores > 0].copy()
                if not matched_df.empty:
                    matched_df["match_score"] = scores[scores > 0]
                    if min_rating:
                        matched_df = matched_df[matched_df["vote_average"] >= min_rating]
                    top_matches = matched_df.sort_values(by="match_score", ascending=False).head(8)
                    for _, row in top_matches.iterrows():
                        mid = int(row["id"])
                        if mid not in seen_ids:
                            seen_ids.add(mid)
                            poster_path = row.get("poster_path")
                            poster_url = f"https://image.tmdb.org/t/p/w342{poster_path}" if (poster_path and "placeholder" not in str(poster_path)) else None
                            raw_genres = row.get("genre_names")
                            genre_list = [str(g) for g in (raw_genres.tolist() if hasattr(raw_genres, "tolist") else raw_genres)] if raw_genres is not None else ["Cinema"]
                            raw_dirs = row.get("director_names")
                            dir_list = [str(d) for d in (raw_dirs.tolist() if hasattr(raw_dirs, "tolist") else raw_dirs)] if raw_dirs is not None else []
                            candidates.append({
                                "id": mid,
                                "tmdb_id": int(row.get("tmdb_id", mid)),
                                "title": row.get("title"),
                                "year": str(row.get("release_date", ""))[:4] or "2020",
                                "rating": float(row.get("vote_average", 7.5)),
                                "genres": genre_list,
                                "director": dir_list[0] if dir_list else "Various",
                                "overview": str(row.get("overview", ""))[:180] + "...",
                                "poster_path": poster_path,
                                "poster_url": poster_url,
                            })

    # 3. TMDB fallback (genre discover & search)
    if len(candidates) < 4:
        # If genre found, discover by genre
        if gid:
            try:
                g_items = await tmdb_svc.discover(genre_id=gid, sort_by="popularity.desc", page=1)
                for m in g_items[:6]:
                    tid = int(m.get("id", 0))
                    if tid not in seen_ids:
                        seen_ids.add(tid)
                        poster = m.get("poster_url") or (f"https://image.tmdb.org/t/p/w342{m.get('poster_path')}" if m.get("poster_path") else None)
                        candidates.append({
                            "id": tid,
                            "tmdb_id": tid,
                            "title": m.get("title"),
                            "year": str(m.get("release_date", ""))[:4] or "2020",
                            "rating": float(m.get("vote_average", 7.0)),
                            "genres": m.get("genre_names", []),
                            "director": "Various",
                            "overview": str(m.get("overview", ""))[:180] + "...",
                            "poster_path": m.get("poster_path"),
                            "poster_url": poster,
                        })
            except Exception as exc:
                log.warning("tmdb_genre_discover_failed", error=str(exc))

        # Title/keyword search on TMDB
        try:
            tmdb_items = await tmdb_svc.search(query=query, page=1)
            for m in tmdb_items[:6]:
                tid = int(m.get("id", 0))
                if tid not in seen_ids:
                    seen_ids.add(tid)
                    poster = m.get("poster_url") or (f"https://image.tmdb.org/t/p/w342{m.get('poster_path')}" if m.get("poster_path") else None)
                    candidates.append({
                        "id": tid,
                        "tmdb_id": tid,
                        "title": m.get("title"),
                        "year": str(m.get("release_date", ""))[:4] or "2020",
                        "rating": float(m.get("vote_average", 7.0)),
                        "genres": m.get("genre_names", []),
                        "director": "Various",
                        "overview": str(m.get("overview", ""))[:180] + "...",
                        "poster_path": m.get("poster_path"),
                        "poster_url": poster,
                    })
        except Exception as exc:
            log.warning("tmdb_keyword_search_failed", error=str(exc))

    return candidates[:8]


async def tool_get_movie_details(movie_id: int) -> dict:
    """Fetch movie details from parquet or TMDB."""
    df = _get_parquet_df()
    if not df.empty:
        match = df[df["id"] == movie_id]
        if not match.empty:
            d = {k: v.tolist() if hasattr(v, "tolist") else v for k, v in match.iloc[0].to_dict().items()}
            return {
                "id": int(d["id"]),
                "title": d.get("title"),
                "year": str(d.get("release_date", ""))[:4],
                "runtime": d.get("runtime"),
                "rating": float(d.get("vote_average", 7.0)),
                "genres": d.get("genre_names", []),
                "director": d.get("director_names", ["Various"]),
                "overview": d.get("overview"),
            }

    # Fallback to TMDB
    detail = await tmdb_svc.get_detail(movie_id)
    if detail:
        return {
            "id": int(detail.get("id", movie_id)),
            "title": detail.get("title"),
            "year": str(detail.get("release_date", ""))[:4],
            "runtime": detail.get("runtime"),
            "rating": float(detail.get("vote_average", 7.0)),
            "genres": detail.get("genre_names", []),
            "director": detail.get("director_names", []),
            "overview": detail.get("overview"),
        }

    return {"error": f"Movie ID {movie_id} not found."}


async def tool_get_similar_movies(movie_id: int, k: int = 5) -> list[dict]:
    """Find similar titles using Hybrid RecSys."""
    k = min(max(k, 1), 10)
    try:
        hybrid = HybridRecommender()
        scored = hybrid.recommend(seed_ids=[movie_id], k=k)
        if scored:
            df = _get_parquet_df()
            mids = [r.movie_id for r in scored]
            matched = df[df["id"].isin(mids)].copy()
            out = []
            for _, row in matched.iterrows():
                d = {k: v.tolist() if hasattr(v, "tolist") else v for k, v in row.to_dict().items()}
                out.append({
                    "id": int(d["id"]),
                    "title": d.get("title"),
                    "rating": float(d.get("vote_average", 7.0)),
                    "genres": d.get("genre_names", []),
                    "year": str(d.get("release_date", ""))[:4],
                })
            return out
    except Exception as exc:
        log.warning("hybrid_rec_failed_in_tool", error=str(exc))

    # TMDB similar fallback
    tmdb_sim = await tmdb_svc.get_similar(movie_id, page=1)
    return [
        {
            "id": int(m["id"]),
            "title": m.get("title"),
            "rating": float(m.get("vote_average", 7.0)),
            "genres": m.get("genre_names", []),
            "year": str(m.get("release_date", ""))[:4],
        }
        for m in tmdb_sim[:k]
    ]


async def tool_get_user_taste_profile(user_id: int | None, session: AsyncSession | None) -> dict:
    """Fetch user's liked titles and favorite genres from database."""
    if not user_id or not session:
        return {
            "status": "anonymous",
            "message": "User is browsing anonymously. Showing broad popular taste profile.",
            "top_genres": ["Sci-Fi", "Action", "Drama"],
        }

    # Fetch ratings & favorites
    res_fav = await session.execute(select(Favorite.movie_id).where(Favorite.user_id == user_id).limit(10))
    fav_ids = res_fav.scalars().all()

    res_rat = await session.execute(
        select(Rating.movie_id, Rating.rating).where(Rating.user_id == user_id).order_by(Rating.rating.desc()).limit(10)
    )
    rated_pairs = res_rat.all()

    df = _get_parquet_df()
    sample_titles = []
    genre_counts: dict[str, int] = {}

    for mid in fav_ids:
        match = df[df["id"] == mid]
        if not match.empty:
            sample_titles.append(match.iloc[0]["title"])
            for g in match.iloc[0]["genre_names"]:
                genre_counts[g] = genre_counts.get(g, 0) + 1

    top_genres = sorted(genre_counts.keys(), key=lambda g: genre_counts[g], reverse=True)[:4]

    return {
        "status": "authenticated",
        "favorites_count": len(fav_ids),
        "favorite_samples": sample_titles[:5],
        "top_genres": top_genres or ["Drama", "Sci-Fi", "Thriller"],
    }


async def tool_compare_movies(movie_id_a: int, movie_id_b: int) -> dict:
    """Compare two movies side by side."""
    meta_a = await tool_get_movie_details(movie_id_a)
    meta_b = await tool_get_movie_details(movie_id_b)

    if "error" in meta_a or "error" in meta_b:
        return {"error": "One or both movie IDs could not be resolved."}

    genres_a = set(meta_a.get("genres", []))
    genres_b = set(meta_b.get("genres", []))
    shared_genres = list(genres_a & genres_b)

    return {
        "movie_a": {
            "title": meta_a.get("title"),
            "year": meta_a.get("year"),
            "rating": meta_a.get("rating"),
            "runtime": meta_a.get("runtime"),
            "director": meta_a.get("director"),
            "genres": meta_a.get("genres"),
        },
        "movie_b": {
            "title": meta_b.get("title"),
            "year": meta_b.get("year"),
            "rating": meta_b.get("rating"),
            "runtime": meta_b.get("runtime"),
            "director": meta_b.get("director"),
            "genres": meta_b.get("genres"),
        },
        "shared_genres": shared_genres,
        "rating_difference": round(abs(meta_a.get("rating", 0) - meta_b.get("rating", 0)), 2),
    }


# ── Tool Dispatch Router ───────────────────────────────────────────────────────

async def dispatch_tool_call(
    tool_name: str,
    arguments: dict[str, Any],
    user_id: int | None = None,
    session: AsyncSession | None = None,
) -> dict[str, Any]:
    """Execute a tool call safely and return structured JSON."""
    log.info("agent_tool_executing", tool=tool_name, args=arguments)

    try:
        if tool_name == "search_movies":
            res = await tool_search_movies(
                query=arguments.get("query", ""),
                language=arguments.get("language"),
                genre=arguments.get("genre"),
                min_rating=arguments.get("min_rating"),
            )
            raw_out = {"results": res}

        elif tool_name == "get_movie_details":
            res = await tool_get_movie_details(int(arguments["movie_id"]))
            raw_out = {"details": res}

        elif tool_name == "get_similar_movies":
            res = await tool_get_similar_movies(
                movie_id=int(arguments["movie_id"]),
                k=int(arguments.get("k", 5)),
            )
            raw_out = {"similar_movies": res}

        elif tool_name == "get_user_taste_profile":
            res = await tool_get_user_taste_profile(user_id=user_id, session=session)
            raw_out = {"profile": res}

        elif tool_name == "compare_movies":
            res = await tool_compare_movies(
                movie_id_a=int(arguments["movie_id_a"]),
                movie_id_b=int(arguments["movie_id_b"]),
            )
            raw_out = {"comparison": res}

        else:
            raw_out = {"error": f"Unknown tool name: {tool_name}"}

        return _sanitize_obj(raw_out)

    except Exception as exc:
        log.error("agent_tool_failed", tool=tool_name, error=str(exc))
        return {"error": f"Tool execution error: {str(exc)}"}


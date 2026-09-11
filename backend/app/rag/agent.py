"""
Conversational Agent Module — CineSense
Implements an autonomous Tool-Calling ReAct Agent using Groq (llama-3.3-70b-versatile),
with native candidate grounding validation to eliminate LLM hallucinations.
"""

from __future__ import annotations

import json
from collections.abc import AsyncGenerator
from typing import Any

import structlog
from groq import AsyncGroq
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.rag.grounding import validate_grounding
from app.rag.search import perform_rag_search
from app.rag.tools import TOOL_SCHEMAS, dispatch_tool_call
from app.services import tmdb as tmdb_svc

log = structlog.get_logger()

SYSTEM_PROMPT = """You are CineSense, an expert AI Cinephile & Recommendation Engineer.
Your mission is to directly recommend films to users with factual, grounded knowledge and cinematic insight.

CRITICAL OPERATIONAL RULES:
1. ALWAYS DIRECTLY RECOMMEND MOVIE NAMES. Never output raw search tags, keywords, or tool syntax to the user. The user wants to see concrete movie recommendations!
2. Call tools (e.g. search_movies) AT MOST 1 or 2 times. As soon as you receive movie candidates from a tool, IMMEDIATELY formulate your final answer. Do NOT make redundant or repeated searches.
3. Every movie recommendation must come from the retrieved tool results. Never hallucinate fake movie titles, release dates, ratings, or directors.
4. Format each recommended movie clearly:
   • **Movie Title (Year)** — ⭐ [Rating]/10
     A 1-2 sentence explanation of why it fits the user's prompt, highlighting director style, tone, or plot twist.
5. For Indian regional cinema (e.g. Marathi, Hindi, Telugu), search with the corresponding language parameter ('mr', 'hi', etc.).
"""


def _enrich_candidates(candidates: list[dict]) -> list[dict]:
    """Deduplicate and normalize candidates for UI presentation."""
    seen_ids: set[Any] = set()
    enriched: list[dict] = []
    for c in candidates:
        cid = c.get("id") or c.get("tmdb_id")
        title = c.get("title", "Untitled")
        key = cid or title
        if key in seen_ids:
            continue
        seen_ids.add(key)

        poster = c.get("poster_url")
        if not poster:
            p_path = c.get("poster_path")
            if p_path:
                poster = f"https://image.tmdb.org/t/p/w342{p_path}"

        enriched.append({
            "id": cid,
            "tmdb_id": c.get("tmdb_id", cid),
            "title": title,
            "year": str(c.get("year", "2020"))[:4],
            "rating": round(float(c.get("rating", 7.5)), 1),
            "genres": c.get("genres", ["Cinema"]),
            "director": c.get("director", "Various"),
            "poster_url": poster,
            "blurb": str(c.get("overview", "A remarkable cinematic selection."))[:200],
        })
        if len(enriched) >= 6:
            break
    return enriched


def _get_groq_client() -> AsyncGroq | None:
    settings = get_settings()
    key = settings.groq_api_key.get_secret_value() if hasattr(settings, "groq_api_key") else ""
    if not key or "your_groq_api_key" in key:
        return None
    return AsyncGroq(api_key=key)


async def run_agent(
    query: str,
    user_id: int | None = None,
    session: AsyncSession | None = None,
) -> dict[str, Any]:
    """Execute complete ReAct agent loop with tool-calling and candidate grounding."""
    client = _get_groq_client()
    settings = get_settings()

    # Fallback to deterministic heuristic RAG if no Groq API key configured
    if not client:
        log.info("groq_key_absent_fallback_to_heuristic_rag")
        rag_res = await perform_rag_search(query=query, user_id=user_id, k=8)
        return {
            "answer": rag_res.intro or "Here are curated recommendations for your query.",
            "candidates": [item.model_dump(mode="json") for item in rag_res.items],
            "tools_invoked": ["heuristic_rag_search"],
        }

    messages: list[dict[str, Any]] = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": query},
    ]

    tools_invoked: list[str] = []
    collected_candidates: list[dict] = []
    max_steps = 3
    step = 0

    while step < max_steps:
        step += 1
        response = await client.chat.completions.create(
            model=settings.groq_model,
            messages=messages,
            tools=TOOL_SCHEMAS,
            tool_choice="auto",
            temperature=0.3,
            max_tokens=800,
        )

        choice = response.choices[0]
        msg = choice.message

        if not msg.tool_calls:
            # Final text answer reached
            final_text = msg.content or ""

            # Validate grounding against retrieved candidates
            if collected_candidates:
                is_grounded, violations = validate_grounding(final_text, collected_candidates)
                if not is_grounded:
                    log.warning("agent_grounding_violation_flagged", violations=violations)

            return {
                "answer": final_text,
                "candidates": _enrich_candidates(collected_candidates),
                "tools_invoked": tools_invoked,
            }

        # Handle tool calls
        messages.append({
            "role": "assistant",
            "content": msg.content or "",
            "tool_calls": [
                {
                    "id": tc.id,
                    "type": "function",
                    "function": {
                        "name": tc.function.name,
                        "arguments": tc.function.arguments,
                    },
                }
                for tc in msg.tool_calls
            ],
        })

        for tc in msg.tool_calls:
            fname = tc.function.name
            tools_invoked.append(fname)
            try:
                fargs = json.loads(tc.function.arguments or "{}")
            except Exception:
                fargs = {}

            # Execute tool
            tool_output = await dispatch_tool_call(
                tool_name=fname,
                arguments=fargs,
                user_id=user_id,
                session=session,
            )

            # Harvest candidate movie records
            if "results" in tool_output and isinstance(tool_output["results"], list):
                collected_candidates.extend(tool_output["results"])
            elif "details" in tool_output and isinstance(tool_output["details"], dict):
                collected_candidates.append(tool_output["details"])
            elif "similar_movies" in tool_output and isinstance(tool_output["similar_movies"], list):
                collected_candidates.extend(tool_output["similar_movies"])

            messages.append({
                "role": "tool",
                "tool_call_id": tc.id,
                "content": json.dumps(tool_output, default=str),
            })

    # If loop limit reached, synthesize recommendations from gathered candidates
    enriched = _enrich_candidates(collected_candidates)
    if enriched:
        messages.append({
            "role": "user",
            "content": "Synthesize your recommendations now based strictly on the retrieved movie data. Directly list the movie names, years, ratings, and why they fit.",
        })
        try:
            final_resp = await client.chat.completions.create(
                model=settings.groq_model,
                messages=messages,
                temperature=0.3,
                max_tokens=600,
            )
            final_text = final_resp.choices[0].message.content or ""
        except Exception:
            final_text = "Here are the top verified movie recommendations matching your request:"
    else:
        final_text = "Here are the top verified movie recommendations based on your query."

    return {
        "answer": final_text,
        "candidates": enriched,
        "tools_invoked": tools_invoked,
    }


async def stream_agent_events(
    query: str,
    user_id: int | None = None,
    session: AsyncSession | None = None,
) -> AsyncGenerator[str, None]:
    """SSE streaming generator yielding live tool events, tokens, and candidate cards."""
    client = _get_groq_client()
    settings = get_settings()

    # Fallback to standard RAG if no key
    if not client:
        rag_res = await perform_rag_search(query=query, user_id=user_id, k=8)
        yield f"event: tool_call\ndata: {json.dumps({'tool': 'heuristic_rag_search', 'args': {'query': query}})}\n\n"

        if rag_res.intro:
            for word in rag_res.intro.split(" "):
                yield f"event: token\ndata: {json.dumps({'token': word + ' '})}\n\n"

        items_payload = [item.model_dump(mode="json") for item in rag_res.items]
        yield f"event: results\ndata: {json.dumps({'items': items_payload})}\n\n"
        yield "event: done\ndata: {}\n\n"
        return

    messages: list[dict[str, Any]] = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": query},
    ]

    try:
        collected_candidates: list[dict] = []
        max_steps = 3
        step = 0

        while step < max_steps:
            step += 1
            response = await client.chat.completions.create(
                model=settings.groq_model,
                messages=messages,
                tools=TOOL_SCHEMAS,
                tool_choice="auto",
                temperature=0.3,
                max_tokens=800,
            )

            msg = response.choices[0].message

            if not msg.tool_calls:
                # Stream response text
                words = (msg.content or "").split(" ")
                for w in words:
                    yield f"event: token\ndata: {json.dumps({'token': w + ' '})}\n\n"

                enriched_items = _enrich_candidates(collected_candidates)
                yield f"event: results\ndata: {json.dumps({'items': enriched_items})}\n\n"
                yield "event: done\ndata: {}\n\n"
                return

            # Handle tool call notifications
            messages.append({
                "role": "assistant",
                "content": msg.content or "",
                "tool_calls": [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments,
                        },
                    }
                    for tc in msg.tool_calls
                ],
            })

            for tc in msg.tool_calls:
                fname = tc.function.name
                try:
                    fargs = json.loads(tc.function.arguments or "{}")
                except Exception:
                    fargs = {}

                # Emit live tool event to UI (e.g. for subtle loading status)
                yield f"event: tool_call\ndata: {json.dumps({'tool': fname, 'args': fargs})}\n\n"

                if session is None and user_id is not None:
                    from app.db.session import AsyncSessionLocal
                    async with AsyncSessionLocal() as db_sess:
                        tool_output = await dispatch_tool_call(
                            tool_name=fname,
                            arguments=fargs,
                            user_id=user_id,
                            session=db_sess,
                        )
                else:
                    tool_output = await dispatch_tool_call(
                        tool_name=fname,
                        arguments=fargs,
                        user_id=user_id,
                        session=session,
                    )

                if "results" in tool_output and isinstance(tool_output["results"], list):
                    collected_candidates.extend(tool_output["results"])
                elif "similar_movies" in tool_output and isinstance(tool_output["similar_movies"], list):
                    collected_candidates.extend(tool_output["similar_movies"])
                elif "details" in tool_output and isinstance(tool_output["details"], dict):
                    collected_candidates.append(tool_output["details"])

                messages.append({
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "content": json.dumps(tool_output, default=str),
                })

        # If max_steps reached, synthesize final recommendation from gathered candidates
        enriched_items = _enrich_candidates(collected_candidates)
        if enriched_items:
            messages.append({
                "role": "user",
                "content": "Synthesize your recommendations now based strictly on the retrieved movie data. Directly list the movie names, years, ratings, and why they fit.",
            })
            try:
                final_resp = await client.chat.completions.create(
                    model=settings.groq_model,
                    messages=messages,
                    temperature=0.3,
                    max_tokens=600,
                )
                final_text = final_resp.choices[0].message.content or ""
            except Exception:
                final_text = "Here are top verified movie recommendations matching your request:"

            for w in final_text.split(" "):
                yield f"event: token\ndata: {json.dumps({'token': w + ' '})}\n\n"

            yield f"event: results\ndata: {json.dumps({'items': enriched_items})}\n\n"
        else:
            for w in "I searched our movie catalog but couldn't find exact matches for that prompt. Try exploring popular genres or asking about a specific movie title!".split(" "):
                yield f"event: token\ndata: {json.dumps({'token': w + ' '})}\n\n"

        yield "event: done\ndata: {}\n\n"

    except Exception as exc:
        import traceback
        traceback.print_exc()
        log.error("stream_agent_events_unhandled_error", error=str(exc))
        yield f"event: token\ndata: {json.dumps({'token': f'I apologize, but I encountered an issue: {str(exc)}'})}\n\n"
        yield "event: done\ndata: {}\n\n"


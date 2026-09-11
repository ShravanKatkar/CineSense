"""
CineSense Background Ingestion Worker
Periodically syncs trending, upcoming, and popular movie metadata from TMDB,
enriches videos and watch providers, and pre-warms the cache.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import UTC, datetime, timedelta
from typing import Any

from app.core.cache import cache_service
from app.core.config import get_settings

log = logging.getLogger(__name__)


class BackgroundIngestionWorker:
    def __init__(self):
        self._task: asyncio.Task | None = None
        self._is_running = False
        self._status = "idle"
        self._last_run_at: datetime | None = None
        self._next_run_at: datetime | None = None
        self._synced_movies_count = 0
        self._last_error: str | None = None

    async def start(self) -> None:
        """Start the background worker loop in asyncio."""
        settings = get_settings()
        if not getattr(settings, "enable_background_sync", True):
            log.info("background_worker: background sync is disabled by configuration.")
            return

        if self._task and not self._task.done():
            return

        self._is_running = True
        self._task = asyncio.create_task(self._run_loop())
        log.info("background_worker: periodic ingestion loop started.")

    async def stop(self) -> None:
        """Gracefully cancel and terminate the background worker loop."""
        self._is_running = False
        if self._task and not self._task.done():
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        self._status = "stopped"
        log.info("background_worker: ingestion loop stopped.")

    async def _run_loop(self) -> None:
        """Periodic loop executing catalog sync on schedule."""
        settings = get_settings()
        interval_hours = getattr(settings, "tmdb_sync_interval_hours", 6)
        interval_seconds = max(interval_hours * 3600, 300)

        # Brief delay on startup before first sync
        await asyncio.sleep(5)

        while self._is_running:
            try:
                self._next_run_at = datetime.now(UTC) + timedelta(seconds=interval_seconds)
                await self.sync_tmdb_feed()
            except asyncio.CancelledError:
                break
            except Exception as exc:
                log.error("background_worker_sync_failed: %s", exc)
                self._last_error = str(exc)
                self._status = "error"

            try:
                await asyncio.sleep(interval_seconds)
            except asyncio.CancelledError:
                break

    async def sync_tmdb_feed(self) -> dict[str, Any]:
        """Execute a full sync pass across TMDB trending, upcoming, and popular titles."""
        from app.services import tmdb as tmdb_svc

        self._status = "running"
        self._last_error = None
        start_time = datetime.now(UTC)
        total_ingested = 0

        log.info("background_worker: beginning TMDB catalog sync pass...")

        try:
            # 1. Fetch Trending movies
            trending_week = await tmdb_svc.get_trending("week")
            trending_day = await tmdb_svc.get_trending("day")
            popular_movies = await tmdb_svc.get_popular(page=1)
            upcoming_movies = await tmdb_svc.get_upcoming(page=1)

            # Deduplicate by tmdb_id / id
            combined = {
                m.get("id"): m
                for m in (trending_week + trending_day + popular_movies + upcoming_movies)
                if m.get("id")
            }

            log.info("background_worker: collected %d unique candidate titles to enrich.", len(combined))

            # 2. Enrich details, trailers, and streaming providers for top candidates
            for movie_id, movie in list(combined.items())[:20]:
                try:
                    # Pre-fetch & warm cache for trailers and providers
                    await tmdb_svc.get_videos(movie_id)
                    await tmdb_svc.get_watch_providers(movie_id)
                    total_ingested += 1
                except Exception as e:
                    log.debug("failed_enrich_movie id=%d: %s", movie_id, e)

            # 3. Pre-warm RecSys popular baseline
            try:
                from app.recsys.baseline.popularity import PopularityRecommender

                pop_rec = PopularityRecommender()
                recs = pop_rec.recommend(k=15)
                await cache_service.set("cinesense:pop_baseline", [r.movie_id for r in recs], ttl_seconds=7200)
            except Exception:
                pass

            self._last_run_at = datetime.now(UTC)
            self._synced_movies_count += total_ingested
            self._status = "idle"

            duration_s = (datetime.now(UTC) - start_time).total_seconds()
            log.info(
                "background_worker: sync pass finished successfully in %.2fs. Enriched %d titles.",
                duration_s,
                total_ingested,
            )

            return {
                "status": "success",
                "synced_count": total_ingested,
                "duration_seconds": round(duration_s, 2),
                "timestamp": self._last_run_at.isoformat(),
            }
        except Exception as exc:
            self._last_error = str(exc)
            self._status = "error"
            log.error("background_worker_sync_exception: %s", exc)
            raise

    async def trigger_manual_sync(self) -> dict[str, Any]:
        """Trigger sync immediately without waiting for interval timer."""
        return await self.sync_tmdb_feed()

    def get_status(self) -> dict[str, Any]:
        """Return worker state and diagnostics."""
        return {
            "worker_active": self._is_running,
            "status": self._status,
            "last_run_at": self._last_run_at.isoformat() if self._last_run_at else None,
            "next_run_at": self._next_run_at.isoformat() if self._next_run_at else None,
            "total_synced_movies": self._synced_movies_count,
            "last_error": self._last_error,
        }


# Global singleton worker instance
ingestion_worker = BackgroundIngestionWorker()

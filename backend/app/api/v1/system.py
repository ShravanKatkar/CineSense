"""
System Management & Worker Diagnostics Endpoints
Provides real-time visibility into the cache tier and background ingestion worker.
"""

from __future__ import annotations

from typing import Any
from fastapi import APIRouter, BackgroundTasks, Query

from app.core.cache import cache_service
from app.services.worker import ingestion_worker

router = APIRouter(prefix="/system", tags=["System & Background Workers"])


@router.get("/status")
async def get_system_status() -> dict[str, Any]:
    """Return health and metrics for the caching layer and background ingestion worker."""
    return {
        "cache": cache_service.stats(),
        "worker": ingestion_worker.get_status(),
    }


@router.post("/sync")
async def trigger_catalog_sync(background_tasks: BackgroundTasks) -> dict[str, str]:
    """Trigger an immediate background sync pass across TMDB trending and upcoming feeds."""
    background_tasks.add_task(ingestion_worker.trigger_manual_sync)
    return {
        "status": "sync_dispatched",
        "message": "Background ingestion pass dispatched successfully.",
    }


@router.post("/cache/clear")
async def clear_cache(prefix: str = Query("", description="Optional prefix to filter keys to clear")) -> dict[str, str]:
    """Flush cache entries (all or matching prefix)."""
    await cache_service.clear(prefix=prefix)
    return {
        "status": "cleared",
        "prefix": prefix or "all",
    }

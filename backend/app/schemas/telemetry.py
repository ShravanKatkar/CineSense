from datetime import datetime
from typing import Any
from pydantic import BaseModel, Field


class InteractionFeedbackIn(BaseModel):
    event_type: str = Field(..., description="Type of event: click, trailer_watch, favorite, rate, drawer_view, search_select")
    movie_id: int
    session_id: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime | None = None


class FeedbackResponse(BaseModel):
    status: str = "success"
    event_id: str
    session_total: int


class SessionTuneRequest(BaseModel):
    seed_ids: list[int] = Field(default_factory=list, description="Recent movie IDs interacted with in this session")
    k: int = Field(default=12, ge=1, le=30)

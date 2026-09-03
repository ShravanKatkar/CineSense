from datetime import datetime

from pydantic import BaseModel, Field

from app.schemas.movies import MovieOut


class ScoredMovieItemOut(MovieOut):
    score: float | None = None
    sources: dict[str, int] = Field(default_factory=dict)
    reason: str | None = None


class RecommendationRowOut(BaseModel):
    title: str
    seed_movie_id: int | None = None
    strategy: str
    items: list[ScoredMovieItemOut]


class RecommendationFeedOut(BaseModel):
    rows: list[RecommendationRowOut]
    strategy: str
    cold_start: bool
    generated_at: datetime

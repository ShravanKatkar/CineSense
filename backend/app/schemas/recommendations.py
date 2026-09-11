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


class WatchTonightRequest(BaseModel):
    available_time: str = Field(default="standard", description="quick (<90m), standard (90-120m), or epic (>120m)")
    mood: str = Field(default="thrilling", description="thrilling, feel_good, deep, mind_bending, scary")
    company: str = Field(default="solo", description="solo, date_night, friends, family")
    language: str = Field(default="any", description="any, en, hi, mr, te, ta, etc.")


class WatchTonightResponse(BaseModel):
    night_vibe_summary: str
    recommendations: list[ScoredMovieItemOut]
    criteria_echo: dict[str, str] = Field(default_factory=dict)


class ParticipantProfile(BaseModel):
    name: str
    favorite_genres: list[str] = Field(default_factory=list)
    seed_movie_titles: list[str] = Field(default_factory=list)


class MovieNightCompromiseItem(ScoredMovieItemOut):
    compromise_score: float = Field(default=0.0, description="Normalized group satisfaction score (0-10)")
    appeal_per_participant: dict[str, str] = Field(default_factory=dict)


class MovieNightRequest(BaseModel):
    participants: list[ParticipantProfile] = Field(..., min_length=2, max_length=5)


class MovieNightResponse(BaseModel):
    group_compatibility_score: int = Field(..., description="Overall group alignment score percentage (0-100)")
    consensus_recommendations: list[MovieNightCompromiseItem]
    explanation: str


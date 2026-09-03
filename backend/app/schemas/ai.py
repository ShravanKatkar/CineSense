from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.movies import MovieOut

GenreEnum = Literal[
    "Action", "Adventure", "Animation", "Comedy", "Crime", "Documentary",
    "Drama", "Family", "Fantasy", "History", "Horror", "Music", "Mystery",
    "Romance", "Science Fiction", "TV Movie", "Thriller", "War", "Western"
]


class SearchIntent(BaseModel):
    semantic_query: str = Field(
        description="Rewritten query focusing on core descriptive theme and mood without filter words."
    )
    similar_to_titles: list[str] = Field(default_factory=list, max_length=3)
    genres_include: list[GenreEnum] = Field(default_factory=list)
    genres_exclude: list[GenreEnum] = Field(default_factory=list)
    year_min: int | None = Field(default=None, ge=1900, le=2030)
    year_max: int | None = Field(default=None, ge=1900, le=2030)
    runtime_max: int | None = Field(default=None, ge=40, le=300)
    max_certification: Literal["G", "PG", "PG-13", "R", "NC-17"] | None = None
    min_rating: float | None = Field(default=None, ge=0, le=10)
    sort_hint: Literal["relevance", "newest", "top_rated", "popular"] = "relevance"
    unsupported_constraints: list[str] = Field(
        default_factory=list,
        description="Constraints requested by user but unsupported by movie database filters."
    )
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)


class Pick(BaseModel):
    movie_id: int
    why: str = Field(
        max_length=280,
        description="One or two sentences explaining why this movie matches the request, based strictly on provided candidate metadata."
    )
    matched_aspects: list[str] = Field(default_factory=list, max_length=4)


class AssistantReply(BaseModel):
    intro: str = Field(max_length=400)
    picks: list[Pick] = Field(min_length=1, max_length=8)
    caveats: list[str] = Field(default_factory=list)
    follow_up: str | None = Field(default=None, max_length=140)


class AISearchRequest(BaseModel):
    query: str = Field(min_length=2, max_length=500)
    k: int = Field(default=12, ge=1, le=50)
    explain: bool = True


class AISearchMeta(BaseModel):
    cached: bool = False
    degraded: bool = False
    degraded_reason: str | None = None
    latency_ms: int
    cost_usd: float
    candidates_considered: int = 0
    grounding_violations: int = 0
    request_id: str | None = None


class AISearchItemOut(MovieOut):
    score: float | None = None
    sources: dict[str, int] = Field(default_factory=dict)
    why: str | None = None
    matched_aspects: list[str] = Field(default_factory=list)


class AISearchResponse(BaseModel):
    query: str
    intent: SearchIntent | None = None
    intro: str | None = None
    items: list[AISearchItemOut]
    caveats: list[str] = Field(default_factory=list)
    meta: AISearchMeta

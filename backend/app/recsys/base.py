from typing import NamedTuple, Protocol

from pydantic import BaseModel, Field


class ScoredMovie(NamedTuple):
    movie_id: int
    score: float
    sources: dict[str, int]  # e.g. {"als": 3, "embedding": 11}


class MovieFilters(BaseModel):
    genres_include: list[str] = Field(default_factory=list)
    genres_exclude: list[str] = Field(default_factory=list)
    year_min: int | None = None
    year_max: int | None = None
    max_certification: str | None = None
    runtime_max: int | None = None
    min_rating: float | None = None


class Recommender(Protocol):
    name: str

    def recommend(
        self,
        *,
        user_id: int | None = None,
        seed_ids: list[int] | None = None,
        filters: MovieFilters | None = None,
        k: int = 12,
    ) -> list[ScoredMovie]:
        ...

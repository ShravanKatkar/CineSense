from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.schemas.movies import MovieOut


class RatingCreate(BaseModel):
    rating: float = Field(ge=0.5, le=5.0)

    @field_validator("rating")
    @classmethod
    def validate_half_step_rating(cls, v: float) -> float:
        if round(v * 2) != v * 2:
            raise ValueError("Rating must be in 0.5 step increments (e.g., 0.5, 1.0, 1.5 ... 5.0)")
        return v


class RatingOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    movie_id: int
    rating: float
    updated_at: datetime
    movie: MovieOut | None = None
    recommendations_stale: bool = True

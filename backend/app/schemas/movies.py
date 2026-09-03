from datetime import date

from pydantic import BaseModel, ConfigDict, Field, computed_field

TMDB_IMAGE_BASE = "https://image.tmdb.org/t/p"


class PersonOut(BaseModel):
    id: int
    name: str
    character: str | None = None
    job: str | None = None
    profile_url: str | None = None


class MovieOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    tmdb_id: int
    title: str
    original_title: str | None = None
    release_date: date | None = None
    runtime: int | None = None
    certification: str | None = None
    poster_path: str | None = None
    backdrop_path: str | None = None
    vote_average: float | None = None
    vote_count: int = 0
    weighted_rating: float | None = None
    genres: list[str] = Field(default_factory=list, validation_alias="genre_names")
    user_rating: float | None = None
    is_favorite: bool = False

    @computed_field
    def release_year(self) -> int | None:
        return self.release_date.year if self.release_date else None

    @computed_field
    def poster_url(self) -> str:
        if not self.poster_path or "placeholder" in self.poster_path.lower():
            return "https://images.unsplash.com/photo-1489599849927-2ee91cede3ba?w=500&q=80"
        if self.poster_path.startswith("http"):
            return self.poster_path
        return f"{TMDB_IMAGE_BASE}/w342{self.poster_path}"

    @computed_field
    def backdrop_url(self) -> str:
        if not self.backdrop_path or "placeholder" in self.backdrop_path.lower():
            return "https://images.unsplash.com/photo-1517604931442-7e0c8ed2963c?w=1280&q=80"
        if self.backdrop_path.startswith("http"):
            return self.backdrop_path
        return f"{TMDB_IMAGE_BASE}/w1280{self.backdrop_path}"


class MovieDetailOut(MovieOut):
    overview: str | None = None
    tagline: str | None = None
    original_language: str | None = None
    directors: list[str] = Field(default_factory=list, validation_alias="director_names")
    top_cast: list[PersonOut] = Field(default_factory=list)
    keywords: list[str] = Field(default_factory=list)


class PaginatedMoviesOut(BaseModel):
    items: list[MovieOut]
    page: int
    page_size: int
    total: int
    has_next: bool

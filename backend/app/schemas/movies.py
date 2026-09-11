from datetime import date

from pydantic import BaseModel, ConfigDict, Field, computed_field, model_validator

TMDB_IMAGE_BASE = "https://image.tmdb.org/t/p"


class PersonOut(BaseModel):
    id: int
    name: str
    character: str | None = None
    job: str | None = None
    profile_url: str | None = None


class MovieOut(BaseModel):
    """
    Unified movie schema that accepts data from both:
      - the local movies.parquet  (movielens_id → id, genre_names alias)
      - the TMDB service          (id == tmdb_id, genre_names key)
    """
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: int
    # tmdb_id may equal id (TMDB source) or be a separate field (parquet source)
    tmdb_id: int = 0
    title: str
    original_title: str | None = None
    release_date: date | str | None = None
    runtime: int | None = None
    certification: str | None = None
    poster_path: str | None = None
    backdrop_path: str | None = None
    vote_average: float | None = None
    vote_count: int = 0
    weighted_rating: float | None = None
    popularity: float = 0.0
    # Accept "genre_names" or "genres" key from TMDB service dict
    genres: list[str] = Field(default_factory=list, validation_alias="genre_names")
    user_rating: float | None = None
    is_favorite: bool = False
    # Pre-computed URLs passed directly from the TMDB service (optional)
    _poster_url_override: str | None = None
    _backdrop_url_override: str | None = None

    @model_validator(mode="before")
    @classmethod
    def _coerce_fields(cls, data: dict) -> dict:
        """
        Normalise differences between the parquet and TMDB data shapes:
        - If genre_names is absent but genres is present, copy it over.
        - If tmdb_id is 0, set it equal to id.
        - Convert numpy arrays or iterables into clean Python lists.
        - Accept pre-built poster_url / backdrop_url from the TMDB service.
        """
        if isinstance(data, dict):
            # Convert numpy arrays or iterables into lists safely
            for key in ("genre_names", "genres", "directors", "director_names", "keywords"):
                val = data.get(key)
                if val is not None and hasattr(val, "tolist"):
                    data[key] = val.tolist()
                elif isinstance(val, (set, tuple)):
                    data[key] = list(val)

            g_names = data.get("genre_names")
            has_g_names = g_names is not None and len(g_names) > 0
            if not has_g_names and data.get("genres"):
                data["genre_names"] = data["genres"]

            tmdb_val = data.get("tmdb_id")
            if tmdb_val is None or tmdb_val == 0:
                data["tmdb_id"] = data.get("id", 0)
        return data

    @computed_field
    def release_year(self) -> int | None:
        if not self.release_date:
            return None
        try:
            if isinstance(self.release_date, date):
                return self.release_date.year
            return int(str(self.release_date)[:4])
        except Exception:
            return None

    @computed_field
    def poster_url(self) -> str:
        if not self.poster_path:
            return ""
        if "placeholder" in self.poster_path.lower():
            return ""
        if self.poster_path.startswith("http"):
            return self.poster_path
        return f"{TMDB_IMAGE_BASE}/w342{self.poster_path}"

    @computed_field
    def backdrop_url(self) -> str:
        if not self.backdrop_path:
            return ""
        if "placeholder" in self.backdrop_path.lower():
            return ""
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


class MovieCompareRequest(BaseModel):
    movie_id_a: int
    movie_id_b: int


class MovieMetricComparison(BaseModel):
    pacing: float = Field(..., ge=0.0, le=10.0, description="Pacing score from 0 to 10")
    visual_spectacle: float = Field(..., ge=0.0, le=10.0, description="Visual spectacle score from 0 to 10")
    emotional_depth: float = Field(..., ge=0.0, le=10.0, description="Emotional depth score from 0 to 10")
    story_complexity: float = Field(..., ge=0.0, le=10.0, description="Story complexity score from 0 to 10")
    rewatchability: float = Field(..., ge=0.0, le=10.0, description="Rewatchability score from 0 to 10")


class MovieCompareResponse(BaseModel):
    movie_a: MovieDetailOut
    movie_b: MovieDetailOut
    metrics_a: MovieMetricComparison
    metrics_b: MovieMetricComparison
    tradeoffs: list[str] = Field(default_factory=list)
    winner_for_mood: dict[str, str] = Field(default_factory=dict)
    ai_verdict: str


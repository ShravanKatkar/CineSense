from datetime import date

from sqlalchemy import (
    ARRAY,
    BOOLEAN,
    DATE,
    NUMERIC,
    SMALLINT,
    TEXT,
    VARCHAR,
    ForeignKey,
    Integer,
    PrimaryKeyConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin


class Movie(Base, TimestampMixin):
    __tablename__ = "movies"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    tmdb_id: Mapped[int] = mapped_column(Integer, unique=True, nullable=False, index=True)
    movielens_id: Mapped[int | None] = mapped_column(Integer, unique=True, nullable=True, index=True)
    imdb_id: Mapped[str | None] = mapped_column(VARCHAR(15), nullable=True)

    title: Mapped[str] = mapped_column(TEXT, nullable=False)
    original_title: Mapped[str | None] = mapped_column(TEXT, nullable=True)
    overview: Mapped[str | None] = mapped_column(TEXT, nullable=True)
    tagline: Mapped[str | None] = mapped_column(TEXT, nullable=True)

    release_date: Mapped[date | None] = mapped_column(DATE, nullable=True)
    runtime: Mapped[int | None] = mapped_column(SMALLINT, nullable=True)
    original_language: Mapped[str | None] = mapped_column(VARCHAR(5), nullable=True)
    certification: Mapped[str | None] = mapped_column(VARCHAR(10), nullable=True)
    adult: Mapped[bool] = mapped_column(BOOLEAN, default=False, nullable=False)

    poster_path: Mapped[str | None] = mapped_column(VARCHAR(120), nullable=True)
    backdrop_path: Mapped[str | None] = mapped_column(VARCHAR(120), nullable=True)

    vote_average: Mapped[float | None] = mapped_column(NUMERIC(4, 2), nullable=True)
    vote_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    popularity: Mapped[float | None] = mapped_column(NUMERIC(10, 4), nullable=True)
    weighted_rating: Mapped[float | None] = mapped_column(NUMERIC(5, 3), nullable=True, index=True)

    genre_names: Mapped[list[str]] = mapped_column(ARRAY(TEXT), default=list, nullable=False)
    director_names: Mapped[list[str]] = mapped_column(ARRAY(TEXT), default=list, nullable=False)

    document: Mapped[str | None] = mapped_column(TEXT, nullable=True)
    embedding_document: Mapped[str | None] = mapped_column(TEXT, nullable=True)
    document_sha256: Mapped[str | None] = mapped_column(VARCHAR(64), nullable=True)
    metadata_complete: Mapped[bool] = mapped_column(BOOLEAN, default=True, nullable=False)

    # Relationships
    movie_genres = relationship("MovieGenre", back_populates="movie", cascade="all, delete-orphan")
    cast = relationship("MovieCast", back_populates="movie", cascade="all, delete-orphan")
    crew = relationship("MovieCrew", back_populates="movie", cascade="all, delete-orphan")
    keywords = relationship("MovieKeyword", back_populates="movie", cascade="all, delete-orphan")
    embedding = relationship("MovieEmbedding", back_populates="movie", uselist=False, cascade="all, delete-orphan")


class Genre(Base):
    __tablename__ = "genres"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    tmdb_genre_id: Mapped[int] = mapped_column(Integer, unique=True, nullable=False)
    name: Mapped[str] = mapped_column(VARCHAR(50), unique=True, nullable=False)


class MovieGenre(Base):
    __tablename__ = "movie_genres"
    __table_args__ = (PrimaryKeyConstraint("movie_id", "genre_id"),)

    movie_id: Mapped[int] = mapped_column(Integer, ForeignKey("movies.id", ondelete="CASCADE"), nullable=False)
    genre_id: Mapped[int] = mapped_column(Integer, ForeignKey("genres.id", ondelete="CASCADE"), nullable=False)

    movie = relationship("Movie", back_populates="movie_genres")


class Person(Base):
    __tablename__ = "people"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    tmdb_person_id: Mapped[int] = mapped_column(Integer, unique=True, nullable=False)
    name: Mapped[str] = mapped_column(TEXT, nullable=False)
    profile_path: Mapped[str | None] = mapped_column(VARCHAR(120), nullable=True)


class MovieCast(Base):
    __tablename__ = "movie_cast"
    __table_args__ = (PrimaryKeyConstraint("movie_id", "person_id", "cast_order"),)

    movie_id: Mapped[int] = mapped_column(Integer, ForeignKey("movies.id", ondelete="CASCADE"), nullable=False)
    person_id: Mapped[int] = mapped_column(Integer, ForeignKey("people.id", ondelete="CASCADE"), nullable=False)
    character: Mapped[str | None] = mapped_column(TEXT, nullable=True)
    cast_order: Mapped[int] = mapped_column(SMALLINT, nullable=False)

    movie = relationship("Movie", back_populates="cast")


class MovieCrew(Base):
    __tablename__ = "movie_crew"
    __table_args__ = (PrimaryKeyConstraint("movie_id", "person_id", "job"),)

    movie_id: Mapped[int] = mapped_column(Integer, ForeignKey("movies.id", ondelete="CASCADE"), nullable=False)
    person_id: Mapped[int] = mapped_column(Integer, ForeignKey("people.id", ondelete="CASCADE"), nullable=False)
    job: Mapped[str] = mapped_column(VARCHAR(60), nullable=False)

    movie = relationship("Movie", back_populates="crew")


class Keyword(Base):
    __tablename__ = "keywords"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    tmdb_keyword_id: Mapped[int] = mapped_column(Integer, unique=True, nullable=False)
    name: Mapped[str] = mapped_column(VARCHAR(100), nullable=False)


class MovieKeyword(Base):
    __tablename__ = "movie_keywords"
    __table_args__ = (PrimaryKeyConstraint("movie_id", "keyword_id"),)

    movie_id: Mapped[int] = mapped_column(Integer, ForeignKey("movies.id", ondelete="CASCADE"), nullable=False)
    keyword_id: Mapped[int] = mapped_column(Integer, ForeignKey("keywords.id", ondelete="CASCADE"), nullable=False)

    movie = relationship("Movie", back_populates="keywords")

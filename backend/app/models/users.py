from datetime import datetime

from sqlalchemy import (
    BOOLEAN,
    NUMERIC,
    SMALLINT,
    VARCHAR,
    BigInteger,
    DateTime,
    ForeignKey,
    Integer,
    PrimaryKeyConstraint,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(VARCHAR(255), unique=True, nullable=False, index=True)
    username: Mapped[str] = mapped_column(VARCHAR(40), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(VARCHAR(255), nullable=False)

    is_active: Mapped[bool] = mapped_column(BOOLEAN, default=True, nullable=False)
    is_seed: Mapped[bool] = mapped_column(BOOLEAN, default=False, nullable=False)
    movielens_uid: Mapped[int | None] = mapped_column(Integer, unique=True, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    ratings = relationship("Rating", back_populates="user", cascade="all, delete-orphan")
    favorites = relationship("Favorite", back_populates="user", cascade="all, delete-orphan")
    history = relationship("WatchHistory", back_populates="user", cascade="all, delete-orphan")


class Rating(Base, TimestampMixin):
    __tablename__ = "ratings"
    __table_args__ = (UniqueConstraint("user_id", "movie_id", name="uq_user_movie_rating"),)

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    movie_id: Mapped[int] = mapped_column(Integer, ForeignKey("movies.id", ondelete="CASCADE"), nullable=False, index=True)
    rating: Mapped[float] = mapped_column(NUMERIC(2, 1), nullable=False)

    user = relationship("User", back_populates="ratings")


class Favorite(Base):
    __tablename__ = "favorites"
    __table_args__ = (PrimaryKeyConstraint("user_id", "movie_id"),)

    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    movie_id: Mapped[int] = mapped_column(Integer, ForeignKey("movies.id", ondelete="CASCADE"), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    user = relationship("User", back_populates="favorites")


class WatchHistory(Base):
    __tablename__ = "watch_history"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    movie_id: Mapped[int] = mapped_column(Integer, ForeignKey("movies.id", ondelete="CASCADE"), nullable=False, index=True)
    watched_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    progress: Mapped[int | None] = mapped_column(SMALLINT, default=100, nullable=True)

    user = relationship("User", back_populates="history")

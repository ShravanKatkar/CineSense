from datetime import datetime

from pgvector.sqlalchemy import Vector
from sqlalchemy import SMALLINT, VARCHAR, DateTime, ForeignKey, Integer, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class MovieEmbedding(Base):
    __tablename__ = "movie_embeddings"

    movie_id: Mapped[int] = mapped_column(Integer, ForeignKey("movies.id", ondelete="CASCADE"), primary_key=True)
    embedding: Mapped[list[float]] = mapped_column(Vector(512), nullable=False)
    model: Mapped[str] = mapped_column(VARCHAR(60), default="voyage-4-lite", nullable=False)
    dim: Mapped[int] = mapped_column(SMALLINT, default=512, nullable=False)
    document_sha256: Mapped[str] = mapped_column(VARCHAR(64), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    movie = relationship("Movie", back_populates="embedding")

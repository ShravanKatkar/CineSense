from datetime import datetime

from pgvector.sqlalchemy import Vector
from sqlalchemy import JSON, TEXT, VARCHAR, DateTime, Integer, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class IntentCache(Base):
    __tablename__ = "intent_cache"

    query_hash: Mapped[str] = mapped_column(VARCHAR(64), primary_key=True)
    normalized_query: Mapped[str] = mapped_column(TEXT, nullable=False)
    intent: Mapped[dict] = mapped_column(JSON, nullable=False)
    model: Mapped[str] = mapped_column(VARCHAR(60), default="claude-opus-5", nullable=False)
    hit_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class EmbeddingCache(Base):
    __tablename__ = "embedding_cache"

    text_hash: Mapped[str] = mapped_column(VARCHAR(64), primary_key=True)
    model: Mapped[str] = mapped_column(VARCHAR(60), default="voyage-4-lite", nullable=False)
    embedding: Mapped[list[float]] = mapped_column(Vector(512), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

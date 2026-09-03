from datetime import datetime

from sqlalchemy import (
    BOOLEAN,
    JSON,
    NUMERIC,
    REAL,
    SMALLINT,
    VARCHAR,
    BigInteger,
    DateTime,
    ForeignKey,
    Integer,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class LLMCall(Base):
    __tablename__ = "llm_calls"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    endpoint: Mapped[str] = mapped_column(VARCHAR(60), nullable=False)
    model: Mapped[str] = mapped_column(VARCHAR(60), nullable=False)

    input_tokens: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    output_tokens: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    cache_read_tokens: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    cache_creation_tokens: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    latency_ms: Mapped[int] = mapped_column(Integer, nullable=False)
    cost_usd: Mapped[float] = mapped_column(NUMERIC(10, 6), nullable=False)

    ok: Mapped[bool] = mapped_column(BOOLEAN, default=True, nullable=False)
    error_code: Mapped[str | None] = mapped_column(VARCHAR(40), nullable=True)
    request_id: Mapped[str | None] = mapped_column(VARCHAR(60), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)


class RecommendationLog(Base):
    __tablename__ = "recommendation_log"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    movie_id: Mapped[int] = mapped_column(Integer, ForeignKey("movies.id", ondelete="CASCADE"), nullable=False)

    strategy: Mapped[str] = mapped_column(VARCHAR(30), nullable=False)
    rank: Mapped[int] = mapped_column(SMALLINT, nullable=False)
    score: Mapped[float | None] = mapped_column(REAL, nullable=True)
    sources: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    clicked: Mapped[bool] = mapped_column(BOOLEAN, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)

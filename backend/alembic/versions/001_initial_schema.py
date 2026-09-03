"""initial schema

Revision ID: 001_initial_schema
Revises: 
Create Date: 2026-09-03 21:10:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector

revision: str = "001_initial_schema"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Enable pgvector extension
    op.execute("CREATE EXTENSION IF NOT EXISTS vector;")

    # Movies table
    op.create_table(
        "movies",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("tmdb_id", sa.Integer(), nullable=False),
        sa.Column("movielens_id", sa.Integer(), nullable=True),
        sa.Column("imdb_id", sa.VARCHAR(length=15), nullable=True),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("original_title", sa.Text(), nullable=True),
        sa.Column("overview", sa.Text(), nullable=True),
        sa.Column("tagline", sa.Text(), nullable=True),
        sa.Column("release_date", sa.Date(), nullable=True),
        sa.Column("runtime", sa.SmallInteger(), nullable=True),
        sa.Column("original_language", sa.VARCHAR(length=5), nullable=True),
        sa.Column("certification", sa.VARCHAR(length=10), nullable=True),
        sa.Column("adult", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("poster_path", sa.VARCHAR(length=120), nullable=True),
        sa.Column("backdrop_path", sa.VARCHAR(length=120), nullable=True),
        sa.Column("vote_average", sa.Numeric(precision=4, scale=2), nullable=True),
        sa.Column("vote_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("popularity", sa.Numeric(precision=10, scale=4), nullable=True),
        sa.Column("weighted_rating", sa.Numeric(precision=5, scale=3), nullable=True),
        sa.Column("genre_names", sa.ARRAY(sa.Text()), nullable=False, server_default="{}"),
        sa.Column("director_names", sa.ARRAY(sa.Text()), nullable=False, server_default="{}"),
        sa.Column("document", sa.Text(), nullable=True),
        sa.Column("embedding_document", sa.Text(), nullable=True),
        sa.Column("document_sha256", sa.VARCHAR(length=64), nullable=True),
        sa.Column("metadata_complete", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tmdb_id"),
        sa.UniqueConstraint("movielens_id"),
    )

    # Users table
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("email", sa.VARCHAR(length=255), nullable=False),
        sa.Column("username", sa.VARCHAR(length=40), nullable=False),
        sa.Column("password_hash", sa.VARCHAR(length=255), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("is_seed", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("movielens_uid", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
        sa.UniqueConstraint("username"),
        sa.UniqueConstraint("movielens_uid"),
    )

    # Ratings table
    op.create_table(
        "ratings",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("movie_id", sa.Integer(), nullable=False),
        sa.Column("rating", sa.Numeric(precision=2, scale=1), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["movie_id"], ["movies.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "movie_id", name="uq_user_movie_rating"),
    )

    # Embeddings table
    op.create_table(
        "movie_embeddings",
        sa.Column("movie_id", sa.Integer(), nullable=False),
        sa.Column("embedding", Vector(512), nullable=False),
        sa.Column("model", sa.VARCHAR(length=60), nullable=False, server_default="voyage-4-lite"),
        sa.Column("dim", sa.SmallInteger(), nullable=False, server_default="512"),
        sa.Column("document_sha256", sa.VARCHAR(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["movie_id"], ["movies.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("movie_id"),
    )


def downgrade() -> None:
    op.drop_table("movie_embeddings")
    op.drop_table("ratings")
    op.drop_table("users")
    op.drop_table("movies")

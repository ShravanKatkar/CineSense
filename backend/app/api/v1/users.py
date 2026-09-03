from pathlib import Path

import pandas as pd
from fastapi import APIRouter, Depends, Response
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import get_current_user
from app.core.exceptions import NotFoundError
from app.db.session import get_db_session
from app.models.users import Favorite, Rating, User
from app.recsys.hybrid.profile import UserTasteProfile, compute_user_profile
from app.schemas.movies import MovieOut
from app.schemas.ratings import RatingCreate, RatingOut

router = APIRouter(prefix="/users/me", tags=["User Profile & Activity"])
PROCESSED_DIR = Path("data/processed")
MOVIES_PARQUET = PROCESSED_DIR / "movies.parquet"


def get_movies_dict() -> dict[int, dict]:
    if not MOVIES_PARQUET.exists():
        return {}
    df = pd.read_parquet(MOVIES_PARQUET)
    df["id"] = df["movielens_id"].dropna().astype(int)
    return {int(row["id"]): row.to_dict() for _, row in df.iterrows()}


@router.get("/ratings", response_model=list[RatingOut])
async def get_my_ratings(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    result = await session.execute(
        select(Rating).where(Rating.user_id == current_user.id).order_by(Rating.updated_at.desc())
    )
    ratings = result.scalars().all()
    movies_dict = get_movies_dict()

    out: list[RatingOut] = []
    for r in ratings:
        m_out = MovieOut.model_validate(movies_dict[r.movie_id]) if r.movie_id in movies_dict else None
        out.append(
            RatingOut(
                movie_id=r.movie_id,
                rating=float(r.rating),
                updated_at=r.updated_at,
                movie=m_out,
                recommendations_stale=False,
            )
        )
    return out


@router.put("/ratings/{movie_id}", response_model=RatingOut)
async def upsert_rating(
    movie_id: int,
    body: RatingCreate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    movies_dict = get_movies_dict()
    if movie_id not in movies_dict:
        raise NotFoundError(f"Movie with ID {movie_id} not found.", identifier=str(movie_id))

    result = await session.execute(
        select(Rating).where(Rating.user_id == current_user.id, Rating.movie_id == movie_id)
    )
    existing = result.scalar_one_or_none()

    if existing:
        existing.rating = body.rating
        rating_obj = existing
    else:
        rating_obj = Rating(
            user_id=current_user.id,
            movie_id=movie_id,
            rating=body.rating,
        )
        session.add(rating_obj)

    await session.commit()
    await session.refresh(rating_obj)

    m_out = MovieOut.model_validate(movies_dict[movie_id])
    return RatingOut(
        movie_id=movie_id,
        rating=float(rating_obj.rating),
        updated_at=rating_obj.updated_at,
        movie=m_out,
        recommendations_stale=True,
    )


@router.delete("/ratings/{movie_id}", status_code=204)
async def delete_rating(
    movie_id: int,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    await session.execute(
        delete(Rating).where(Rating.user_id == current_user.id, Rating.movie_id == movie_id)
    )
    await session.commit()
    return Response(status_code=204)


@router.get("/favorites", response_model=list[MovieOut])
async def get_my_favorites(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    result = await session.execute(
        select(Favorite).where(Favorite.user_id == current_user.id).order_by(Favorite.created_at.desc())
    )
    favs = result.scalars().all()
    movies_dict = get_movies_dict()

    items: list[MovieOut] = []
    for f in favs:
        if f.movie_id in movies_dict:
            m_data = dict(movies_dict[f.movie_id])
            m_data["is_favorite"] = True
            items.append(MovieOut.model_validate(m_data))
    return items


@router.post("/favorites/{movie_id}", status_code=201)
async def add_favorite(
    movie_id: int,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    movies_dict = get_movies_dict()
    if movie_id not in movies_dict:
        raise NotFoundError(f"Movie with ID {movie_id} not found.", identifier=str(movie_id))

    result = await session.execute(
        select(Favorite).where(Favorite.user_id == current_user.id, Favorite.movie_id == movie_id)
    )
    if not result.scalar_one_or_none():
        fav = Favorite(user_id=current_user.id, movie_id=movie_id)
        session.add(fav)
        await session.commit()

    return {"status": "added", "movie_id": movie_id}


@router.delete("/favorites/{movie_id}", status_code=204)
async def remove_favorite(
    movie_id: int,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    await session.execute(
        delete(Favorite).where(Favorite.user_id == current_user.id, Favorite.movie_id == movie_id)
    )
    await session.commit()
    return Response(status_code=204)


@router.get("/profile", response_model=UserTasteProfile)
async def get_my_taste_profile(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    r_result = await session.execute(select(Rating).where(Rating.user_id == current_user.id))
    ratings = list(r_result.scalars().all())

    user_ratings_df = pd.DataFrame([{"userId": r.user_id, "movieId": r.movie_id, "rating": float(r.rating)} for r in ratings])
    movies_df = pd.read_parquet(MOVIES_PARQUET)

    return compute_user_profile(current_user.id, user_ratings_df, movies_df)

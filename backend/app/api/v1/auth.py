import uuid
from typing import Annotated

from fastapi import APIRouter, Cookie, Depends, Response
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import get_current_user
from app.core.config import get_settings
from app.core.exceptions import AuthError, ValidationError
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.db.session import get_db_session
from app.models.users import Favorite, Rating, User
from app.schemas.auth import TokenOut, UserCreate, UserLogin, UserOut

router = APIRouter(prefix="/auth", tags=["Auth"])
settings = get_settings()


def set_refresh_cookie(response: Response, refresh_token: str) -> None:
    response.set_cookie(
        key="cinesense_refresh",
        value=refresh_token,
        max_age=settings.refresh_token_days * 86400,
        httponly=True,
        secure=settings.environment == "production",
        samesite="lax",
        path="/api/v1/auth",
    )


@router.post("/register", response_model=TokenOut, status_code=201)
async def register(
    body: UserCreate,
    response: Response,
    session: AsyncSession = Depends(get_db_session),
):
    # Check existing email or username
    existing = await session.execute(
        select(User).where((User.email == body.email.lower()) | (User.username == body.username))
    )
    if existing.scalar_one_or_none():
        raise ValidationError("An account with that email or username already exists.")

    hashed = hash_password(body.password)
    user = User(
        email=body.email.lower(),
        username=body.username,
        password_hash=hashed,
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)

    access_token = create_access_token(user.id, user.email)
    jti = str(uuid.uuid4())
    refresh_token = create_refresh_token(user.id, jti=jti)
    set_refresh_cookie(response, refresh_token)

    user_out = UserOut.model_validate(user)
    return TokenOut(
        access_token=access_token,
        expires_in=settings.access_token_minutes * 60,
        user=user_out,
    )


@router.post("/login", response_model=TokenOut)
async def login(
    body: UserLogin,
    response: Response,
    session: AsyncSession = Depends(get_db_session),
):
    result = await session.execute(select(User).where(User.email == body.email.lower(), User.is_active == True))
    user = result.scalar_one_or_none()

    if not user or not verify_password(body.password, user.password_hash):
        raise AuthError("Invalid email or password")

    # Fetch rating & favorite counts
    n_ratings = (await session.execute(select(func.count()).select_from(Rating).where(Rating.user_id == user.id))).scalar() or 0
    n_favs = (await session.execute(select(func.count()).select_from(Favorite).where(Favorite.user_id == user.id))).scalar() or 0

    access_token = create_access_token(user.id, user.email)
    jti = str(uuid.uuid4())
    refresh_token = create_refresh_token(user.id, jti=jti)
    set_refresh_cookie(response, refresh_token)

    user_out = UserOut(
        id=user.id,
        email=user.email,
        username=user.username,
        is_seed=user.is_seed,
        n_ratings=n_ratings,
        n_favorites=n_favs,
        created_at=user.created_at,
    )

    return TokenOut(
        access_token=access_token,
        expires_in=settings.access_token_minutes * 60,
        user=user_out,
    )


@router.post("/refresh", response_model=TokenOut)
async def refresh_tokens(
    response: Response,
    cinesense_refresh: Annotated[str | None, Cookie()] = None,
    session: AsyncSession = Depends(get_db_session),
):
    if not cinesense_refresh:
        raise AuthError("Missing refresh token cookie")

    try:
        payload = decode_token(cinesense_refresh)
    except Exception as exc:
        raise AuthError(f"Invalid refresh token: {exc}") from exc

    if payload.get("type") != "refresh":
        raise AuthError("Invalid token type")

    user_id = int(payload["sub"])
    result = await session.execute(select(User).where(User.id == user_id, User.is_active == True))
    user = result.scalar_one_or_none()
    if not user:
        raise AuthError("User not found")

    new_access = create_access_token(user.id, user.email)
    new_jti = str(uuid.uuid4())
    new_refresh = create_refresh_token(user.id, jti=new_jti)
    set_refresh_cookie(response, new_refresh)

    n_ratings = (await session.execute(select(func.count()).select_from(Rating).where(Rating.user_id == user.id))).scalar() or 0
    n_favs = (await session.execute(select(func.count()).select_from(Favorite).where(Favorite.user_id == user.id))).scalar() or 0

    user_out = UserOut(
        id=user.id,
        email=user.email,
        username=user.username,
        is_seed=user.is_seed,
        n_ratings=n_ratings,
        n_favorites=n_favs,
        created_at=user.created_at,
    )

    return TokenOut(
        access_token=new_access,
        expires_in=settings.access_token_minutes * 60,
        user=user_out,
    )


@router.post("/logout", status_code=204)
async def logout(response: Response):
    response.delete_cookie(key="cinesense_refresh", path="/api/v1/auth")


@router.get("/me", response_model=UserOut)
async def get_me(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    n_ratings = (await session.execute(select(func.count()).select_from(Rating).where(Rating.user_id == current_user.id))).scalar() or 0
    n_favs = (await session.execute(select(func.count()).select_from(Favorite).where(Favorite.user_id == current_user.id))).scalar() or 0

    return UserOut(
        id=current_user.id,
        email=current_user.email,
        username=current_user.username,
        is_seed=current_user.is_seed,
        n_ratings=n_ratings,
        n_favorites=n_favs,
        created_at=current_user.created_at,
    )

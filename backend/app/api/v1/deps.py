from typing import Annotated

from fastapi import Depends, Header
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AuthError
from app.core.security import decode_token
from app.db.session import get_db_session
from app.models.users import User


async def get_current_user(
    authorization: Annotated[str | None, Header()] = None,
    session: AsyncSession = Depends(get_db_session),
) -> User:
    """Dependency extracting and validating current authenticated user from Bearer header."""
    if not authorization or not authorization.startswith("Bearer "):
        raise AuthError("Missing or invalid Authorization Bearer header")

    token = authorization.split(" ", 1)[1]
    try:
        payload = decode_token(token)
    except Exception as exc:
        raise AuthError(f"Invalid access token: {exc}") from exc

    if payload.get("type") != "access":
        raise AuthError("Invalid token type")

    user_id_str = payload.get("sub")
    if not user_id_str or not user_id_str.isdigit():
        raise AuthError("Invalid token subject")

    user_id = int(user_id_str)
    result = await session.execute(select(User).where(User.id == user_id, User.is_active == True))
    user = result.scalar_one_or_none()

    if not user:
        raise AuthError("User account not found or inactive")

    return user


async def get_optional_user(
    authorization: Annotated[str | None, Header()] = None,
    session: AsyncSession = Depends(get_db_session),
) -> User | None:
    """Dependency returning authenticated User or None if anonymous."""
    if not authorization or not authorization.startswith("Bearer "):
        return None
    try:
        return await get_current_user(authorization=authorization, session=session)
    except AuthError:
        return None


class PaginationParams:
    def __init__(self, page: int = 1, page_size: int = 20):
        self.page = max(1, page)
        self.page_size = min(100, max(1, page_size))
        self.offset = (self.page - 1) * self.page_size

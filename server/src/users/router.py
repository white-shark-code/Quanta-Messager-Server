"""Per-user lookup endpoints.

Currently exposes the public PGP key of any registered user so the
client can decide whether a peer is set up for end-to-end encrypted
messaging before opening a chat with them.

Эндпоинты поиска пользователей.
"""
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from authentication.models import User
from authentication.services import current_user_av
from database import AsyncSession, get_async_session

from .schemas import PublicKeyResponse

router: APIRouter = APIRouter(prefix="/users", tags=["users"])


@router.get(
    path="/{user_id}/public-key",
    response_model=PublicKeyResponse,
)
async def get_user_public_key(
    user_id: UUID,
    user: User = Depends(dependency=current_user_av),
    session: AsyncSession = Depends(dependency=get_async_session),
) -> PublicKeyResponse:
    """Fetch the PGP public key for an arbitrary user.

    Returns ``has_public_key: false`` (and ``public_key: null``)
    when the target user exists but hasn't uploaded a key yet.
    Returns 404 when the user doesn't exist at all.

    The caller's own identity is irrelevant to the response — any
    authenticated user can fetch any other user's public key. That
    is the whole point of a public key.

    Возвращает публичный PGP-ключ пользователя.

    Args:
        user_id: UUID of the user whose key is being requested.
        user: The currently authenticated user (only used to gate
            the endpoint; the value is not echoed in the response).
        session: Async database session.

    Returns:
        The target user's public-key record.

    Raises:
        HTTPException: 404 if the user does not exist.
    """
    target: User | None = await session.get(entity=User, ident=user_id)
    if target is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    has_key: bool = (
        target.public_key is not None and len(target.public_key) > 0
    )
    return PublicKeyResponse(
        user_id=target.id,
        has_public_key=has_key,
        public_key=target.public_key if has_key else None,
    )

"""Authentication API router for PGP key management.

This module provides endpoints for changing user PGP public keys,
including validation and error handling.

Uses GnuPG 2.4+ (RFC 9580-compliant) via :mod:`shared.pgp` for parsing
ASCII-armored OpenPGP keys.

Роутер API аутентификации для управления PGP-ключами.

Модуль предоставляет эндпоинты для изменения PGP публичных ключей пользователей,
включая валидацию и обработку ошибок.

Использует GnuPG 2.4+ (RFC 9580) через :mod:`shared.pgp`.
"""

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status

from database import AsyncSession, get_async_session
from shared.pgp import get_backend

from .models import User
from .schemas import UserReadWithPGP
from .services import current_user_av

auth_router: APIRouter = APIRouter()


@auth_router.post(path="/change-public-key", response_model=UserReadWithPGP)
async def change_public_key(
    new_public_key: UploadFile = File(),
    user: User = Depends(dependency=current_user_av),
    session: AsyncSession = Depends(dependency=get_async_session),
):
    """Change the user's PGP public key.

    Validates the uploaded file via GnuPG ``--import``, ensures only a
    public key (no private), then updates the user record.

    Изменяет PGP публичный ключ пользователя.

    Валидирует файл через ``gpg --import``, проверяет, что прислан
    только публичный ключ, и обновляет запись пользователя.

    Args:
        new_public_key: The uploaded PGP public key file.
        user: The authenticated user.
        session: The database session.

    Raises:
        HTTPException: 422 if file is too large or wrong type.
        HTTPException: 400 if GnuPG cannot import the key.
        HTTPException: 422 if a private key is submitted.

    Returns:
        Updated user data with new public key.
    """
    try:
        size_ok = new_public_key.size is None or new_public_key.size <= 10_000
        type_ok = new_public_key.content_type == "text/plain"
        if not size_ok and not type_ok:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Lagger file PGP",
            )
        pgp_file_as_str: bytes = new_public_key.file.read()

        backend = get_backend()
        fingerprint, is_private = await backend.import_key(pgp_file_as_str)
    except HTTPException:
        raise
    except Exception as e:  # subprocess / GPG failures surface as Python exceptions
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid PGP data: {e}",
        )

    if not fingerprint:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid PGP data: GnuPG could not import the key",
        )

    if is_private:
        await backend.delete_key(fingerprint)
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Don't send private key",
        )

    # Cleanup: the key was imported solely for validation.
    await backend.delete_key(fingerprint)

    user.public_key = pgp_file_as_str

    await session.commit()

    await session.refresh(user)

    return user

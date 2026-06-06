"""Authentication API router for PGP key management.

This module provides endpoints for changing user PGP public keys,
including validation and error handling.

Роутер API аутентификации для управления PGP-ключами.

Модуль предоставляет эндпоинты для изменения PGP публичных ключей пользователей,
включая валидацию и обработку ошибок.
"""


from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from pgpy import PGPKey

from database import AsyncSession, get_async_session

from .models import User
from .schemas import UserReadWithPGP
from .services import current_user_av

auth_router: APIRouter = APIRouter()


@auth_router.post(path='/change-public-key', response_model=UserReadWithPGP)
async def change_public_key(
    new_public_key: UploadFile = File(),
    user: User = Depends(dependency=current_user_av),
    session: AsyncSession = Depends(dependency=get_async_session),
):
    """Change the user's PGP public key.

    Validates the uploaded file, parses the PGP key, and updates the user record.

    Изменяет PGP публичный ключ пользователя.

    Валидирует загруженный файл, парсит PGP-ключ и обновляет запись пользователя.

    Args:
        new_public_key: The uploaded PGP public key file.
        user: The authenticated user.
        session: Async database session.

    Raises:
        HTTPException: 422 if file is too large or wrong type.
        HTTPException: 400 if PGP data is invalid.
        HTTPException: 422 if a private key is submitted.

    Returns:
        Updated user data with new public key.
    """
    try:
        size_ok = new_public_key.size is None or new_public_key.size <= 10_000
        type_ok = new_public_key.content_type == 'text/plain'
        if not size_ok and not type_ok:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail='Lagger file PGP'
            )
        pgp_file_as_str: bytes = new_public_key.file.read()
        public_key_tuple = PGPKey.from_blob(pgp_file_as_str)  # type: ignore[assignment]
        if isinstance(public_key_tuple, tuple):
            public_key: PGPKey = public_key_tuple[0]
        else:
            public_key = public_key_tuple
    except ValueError as e:
        if e.args[0] == 'Expected: ASCII-armored PGP data':
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=e.args[0]
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST
            )
    if not public_key.is_public:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail='Don\'t send private key'
        )

    user.public_key = pgp_file_as_str

    await session.commit()

    await session.refresh(user)

    return user

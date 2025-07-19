from collections import OrderedDict

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
    try:
        if new_public_key.size > 10_000 and new_public_key.content_type != 'text/plain':
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail='Lagger file PGP'
            )
        pgp_file_as_str: bytes = new_public_key.file.read()
        public_key_tuple: tuple[PGPKey, OrderedDict] = PGPKey.from_blob(pgp_file_as_str)
        public_key: PGPKey = public_key_tuple[0]
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

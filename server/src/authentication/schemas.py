from datetime import datetime
from enum import Enum
from uuid import UUID

from fastapi_users import schemas
from pydantic import BaseModel


class Roles(Enum):
    READER: str = "reader"
    USER: str = "user"
    KEYMAN: str = "keyman"
    MODERATOR: str = "moderator"
    SMALL_ADMIN: str = "small_admin"
    ADMIN: str = "admin"

    @classmethod
    def get_default(cls):
        return cls.USER


class UserGroup(BaseModel):
    user_id: UUID
    group_chat_id: UUID
    joined_data: datetime
    role: Roles

class PublicKey(BaseModel):
    public_key: bytes | None

class UserRead(schemas.BaseUser[UUID]):
    pass

class UserReadWithPGP(UserRead, PublicKey):
    pass

class UserCreate(schemas.BaseUserCreate):
    pass


class UserUpdate(schemas.BaseUserUpdate):
    pass

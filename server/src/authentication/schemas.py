"""Authentication schemas for API request/response validation.

This module defines Pydantic schemas and role enums for user authentication,
including user CRUD schemas and PGP public key handling.

Схемы аутентификации для валидации запросов/ответов API.

Модуль определяет Pydantic-схемы и enum ролей для аутентификации пользователей,
включая CRUD-схемы пользователей и работу с PGP-ключами.
"""

from datetime import datetime
from enum import Enum
from uuid import UUID

from fastapi_users import schemas
from pydantic import BaseModel


class Roles(Enum):
    """User roles for access control.

    Роли пользователей для управления доступом.
    """
    READER = "reader"
    USER = "user"
    KEYMAN = "keyman"
    MODERATOR = "moderator"
    SMALL_ADMIN = "small_admin"
    ADMIN = "admin"

    @classmethod
    def get_default(cls):
        """Return the default role for new users.

        Возвращает роль по умолчанию для новых пользователей.
        """
        return cls.USER


class UserGroup(BaseModel):
    """Schema for user-group membership data.

    Схема данных принадлежности пользователя к группе.
    """
    user_id: UUID
    group_chat_id: UUID
    joined_data: datetime
    role: Roles

class PublicKey(BaseModel):
    """Schema for PGP public key.

    Схема для PGP публичного ключа.
    """
    public_key: bytes | None

class UserRead(schemas.BaseUser[UUID]):
    """Schema for reading user data.

    Схема для чтения данных пользователя.
    """
    pass

class UserReadWithPGP(UserRead, PublicKey):
    """Schema for reading user data with PGP public key.

    Схема для чтения данных пользователя с PGP публичным ключом.
    """
    pass

class UserCreate(schemas.BaseUserCreate):
    """Schema for creating a new user.

    Схема для создания нового пользователя.
    """
    pass


class UserUpdate(schemas.BaseUserUpdate):
    """Schema for updating user data.

    Схема для обновления данных пользователя.
    """
    pass

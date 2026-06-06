"""Authentication models for users, groups, and access tokens.

This module defines SQLAlchemy ORM models for user accounts,
user-group relationships, and access token storage.

Модели аутентификации для пользователей, групп и токенов доступа.

Модуль определяет SQLAlchemy ORM-модели для учётных записей пользователей,
связей пользователь-группа и хранения токенов доступа.
"""

from datetime import datetime
from uuid import UUID

from fastapi_users.db import SQLAlchemyBaseUserTableUUID
from fastapi_users_db_sqlalchemy.access_token import SQLAlchemyBaseAccessTokenTableUUID
from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base

from .schemas import Roles


class UserGroup(Base):
    """User-group membership relationship.

    Связь принадлежности пользователя к группе.
    """
    __tablename__: str = "user_groups"

    user_id: Mapped[UUID] = mapped_column(
        ForeignKey(column="user.id"), primary_key=True
    )
    group_chat_id: Mapped[UUID] = mapped_column(
        ForeignKey(column="group_chats.id"), primary_key=True
    )
    joined_data: Mapped[datetime] = mapped_column(
        default=datetime.utcnow, nullable=False
    )
    role: Mapped[Roles] = mapped_column(default=Roles.get_default, nullable=False)


class User(SQLAlchemyBaseUserTableUUID, Base):
    """User accounts table.

    Таблица учётных записей пользователей.
    """
    public_key: Mapped[bytes] = mapped_column(nullable=True)

    groups: Mapped[UUID] = relationship(
        argument="GroupChat", secondary="user_groups", back_populates="users"
    )


class AccessToken(SQLAlchemyBaseAccessTokenTableUUID, Base):
    """Access tokens table for authentication.

    Таблица токенов доступа для аутентификации.
    """

    pass

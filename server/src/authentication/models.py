from datetime import datetime
from uuid import UUID

from fastapi_users.db import SQLAlchemyBaseUserTableUUID
from fastapi_users_db_sqlalchemy.access_token import SQLAlchemyBaseAccessTokenTableUUID
from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base

from .schemas import Roles


class UserGroup(Base):
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
    """Table with users in database."""
    public_key: Mapped[bytes] = mapped_column(nullable=True)

    groups: Mapped[UUID] = relationship(
        argument="GroupChat", secondary="user_groups", back_populates="users"
    )


class AccessToken(SQLAlchemyBaseAccessTokenTableUUID, Base):
    """Table with access tokens in database."""

    pass

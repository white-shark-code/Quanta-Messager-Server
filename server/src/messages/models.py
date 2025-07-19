from datetime import datetime
from uuid import UUID, uuid4

from fastapi_users_db_sqlalchemy.generics import GUID
from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from authentication.models import User
from database import Base


class BasicChat(Base):
    """Abstract class for chat classes"""

    __abstract__: bool = True

    id: Mapped[UUID] = mapped_column(
        GUID,
        primary_key=True,
        default=uuid4
    )
    name: Mapped[str]
    creation_datetime: Mapped[datetime] = mapped_column(
        default=datetime.utcnow, nullable=False
    )


class DialogChat(BasicChat):
    """Table users dialog"""

    __tablename__: str = "dialog_chats"

    user0: Mapped[UUID] = mapped_column(
        ForeignKey(column=User.id, ondelete="CASCADE"), nullable=False
    )
    user1: Mapped[UUID] = mapped_column(
        ForeignKey(column=User.id, ondelete="CASCADE"), nullable=False
    )


class GroupChat(BasicChat):
    """Group chats"""

    __tablename__: str = "group_chats"

    users: Mapped[UUID] = relationship(
        argument="User", secondary="user_groups", back_populates="groups"
    )
    public_key: Mapped[bytes] = mapped_column(nullable=False)


class BasicMessage(Base):
    """Abstract class for messages classes"""

    __abstract__: bool = True

    id: Mapped[UUID] = mapped_column(
        GUID,
        primary_key=True,
        default=uuid4
    )
    owner_id: Mapped[UUID] = mapped_column(ForeignKey(column=User.id), nullable=False)
    encrypted_message: Mapped[bytes] = mapped_column(nullable=False)
    creation_datetime: Mapped[datetime] = mapped_column(
        default=datetime.utcnow, nullable=False
    )


class DialogMessage(BasicMessage):
    """Dialog message class"""

    __tablename__: str = "dialog_messages"

    chat_id: Mapped[UUID] = mapped_column(
        ForeignKey(column=DialogChat.id, ondelete="CASCADE")
    )


class GroupMessage(BasicMessage):
    """Group message class"""

    __tablename__: str = "group_messages"

    chat_id: Mapped[UUID] = mapped_column(
        ForeignKey(column=GroupChat.id, ondelete="CASCADE")
    )

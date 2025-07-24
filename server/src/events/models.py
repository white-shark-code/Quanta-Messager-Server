from uuid import UUID, uuid4

from fastapi_users_db_sqlalchemy.generics import GUID
from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from authentication.models import User
from database import Base
from messages.models import DialogChat, GroupChat


class EventInChat(Base):
    """Abstract class for classes events in chats"""

    __abstract__: bool = True

    id: Mapped[UUID] = mapped_column(
        GUID,
        primary_key = True,
        default = uuid4
    )
    user_id: Mapped[UUID] = mapped_column(
        ForeignKey(
            column = User.id,
            ondelete = "CASCADE"
        ),
        nullable = False
    )
    count: Mapped[int]


class EventInDialogChat(EventInChat):
    """Table with events in dialog chats"""

    __tablename__: str = "dialog_chats_events"

    chat_id: Mapped[UUID] = mapped_column(
        ForeignKey(
            column = DialogChat.id,
            ondelete = "CASCADE"
        ),
        nullable = False
    )


class EventInGroupChat(EventInChat):
    """Table with events in group chats"""

    __tablename__: str = "group_chats_events"

    chat_id: Mapped[UUID] = mapped_column(
        ForeignKey(
            column = GroupChat.id,
            ondelete = "CASCADE"
        ),
        nullable = False
    )

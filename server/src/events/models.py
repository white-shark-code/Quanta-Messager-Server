"""Event models for tracking changes in dialog and group chats.

This module defines SQLAlchemy ORM models that represent events
triggered when new messages arrive in chats. Each event tracks
the user, chat, and a counter of unread items.

Модели событий для отслеживания изменений в диалогах и группах.

Модуль определяет SQLAlchemy ORM-модели, представляющие события,
возникающие при поступлении новых сообщений в чатах. Каждое событие
отслеживает пользователя, чат и счётчик непрочитанных элементов.
"""

from uuid import UUID

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from authentication.models import User
from messages.models import DialogChat, GroupChat
from shared.abstract_sqlalchemy_models import (
    AbstractModelWithCreateAt,
    AbstractModelWithUUID,
)


class EventInChat(
    AbstractModelWithUUID,
    AbstractModelWithCreateAt
):
    """Abstract class for events in chats.

    Базовый абстрактный класс для событий в чатах.
    """

    __abstract__: bool = True

    user_id: Mapped[UUID] = mapped_column(
        ForeignKey(
            column = User.id,
            ondelete = "CASCADE"
        ),
        nullable = False
    )
    count: Mapped[int]


class EventInDialogChat(EventInChat):
    """Events in dialog chats.

    События в диалоговых чатах.
    """

    __tablename__: str = "dialog_chats_events"

    chat_id: Mapped[UUID] = mapped_column(
        ForeignKey(
            column = DialogChat.id,
            ondelete = "CASCADE"
        ),
        nullable = False
    )


class EventInGroupChat(EventInChat):
    """Events in group chats.

    События в групповых чатах.
    """

    __tablename__: str = "group_chats_events"

    chat_id: Mapped[UUID] = mapped_column(
        ForeignKey(
            column = GroupChat.id,
            ondelete = "CASCADE"
        ),
        nullable = False
    )

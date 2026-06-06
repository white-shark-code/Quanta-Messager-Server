"""Services for creating and updating chat events.

This module provides helper functions to increment event counters
when new messages arrive in dialog or group chats.

Сервисы для создания и обновления событий в чатах.

Модуль предоставляет вспомогательные функции для увеличения счётчиков событий
при поступлении новых сообщений в диалоговых или групповых чатах.
"""

from uuid import UUID

from sqlalchemy import ChunkedIteratorResult, Select, select
from sqlalchemy.exc import NoResultFound

from database import AsyncSession

from .models import EventInDialogChat, EventInGroupChat


async def add_event_in_dialog_chat(
    session: AsyncSession,
    chat_id: UUID,
    user_id: UUID
):
    """Add or increment an event counter for a dialog chat.

    If an event already exists for the user and chat, increments the counter.
    Otherwise, creates a new event with count=1.

    Добавляет или увеличивает счётчик событий в диалоговом чате.

    Если событие уже существует для пользователя и чата, увеличивает счётчик.
    Иначе создаёт новое событие с count=1.

    Args:
        session: Async database session.
        chat_id: The dialog chat ID.
        user_id: The user ID to notify.
    """
    try:

        stmt: Select = select(EventInDialogChat).where(
            EventInDialogChat.chat_id == chat_id,
            EventInDialogChat.user_id == user_id
        )

        events_chunked: ChunkedIteratorResult = await session.execute(stmt)

        event: EventInDialogChat = events_chunked.one()

        event.count: int = event.count + 1

    except NoResultFound:

        event: EventInDialogChat = EventInDialogChat(
            chat_id = chat_id,
            user_id = user_id,
            count = 1
        )

        session.add(event)

    await session.flush(objects=[event])


async def add_event_in_group_chat(
    session: AsyncSession,
    chat_id: UUID,
    user_id: UUID
):
    """Add or increment an event counter for a group chat.

    If an event already exists for the user and chat, increments the counter.
    Otherwise, creates a new event with count=1.

    Добавляет или увеличивает счётчик событий в групповом чате.

    Если событие уже существует для пользователя и чата, увеличивает счётчик.
    Иначе создаёт новое событие с count=1.

    Args:
        session: Async database session.
        chat_id: The group chat ID.
        user_id: The user ID to notify.
    """
    try:

        stmt: Select = select(EventInGroupChat).where(
            EventInGroupChat.chat_id == chat_id,
            EventInGroupChat.user_id == user_id
        )

        events_chunked: ChunkedIteratorResult = await session.execute(stmt)

        event: EventInGroupChat = events_chunked.one()

        event.count: int = event.count + 1

    except NoResultFound:

        event: EventInGroupChat = EventInGroupChat(
            chat_id = chat_id,
            user_id = user_id,
            count = 1
        )

        session.add(event)

    await session.flush(objects=[event])

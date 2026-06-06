"""Events API router for managing chat event notifications.

This module provides REST endpoints for retrieving unread event counts
and marking events as read in dialog and group chats.

Роутер API событий для управления уведомлениями о событиях в чатах.

Модуль предоставляет REST-эндпоинты для получения счётчиков непрочитанных
событий и отметки событий как прочитанных в диалоговых и групповых чатах.
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, responses, status
from sqlalchemy import ChunkedIteratorResult, Select, select
from sqlalchemy.exc import NoResultFound

from authentication.models import User
from authentication.services import current_user_av
from database import AsyncSession, get_async_session
from messages.schemas import ListItems

from .models import EventInDialogChat, EventInGroupChat
from .schemas import EventInDialogChat as sc_EventInDialogChat
from .schemas import EventInGroupChat as sc_EventInGroupChat

events: APIRouter = APIRouter(
    prefix='/event'
)


@events.get(
    path = '/dialogs/',
    response_model = ListItems[sc_EventInDialogChat]
)
async def get_dialogs_events(
    user: User = Depends(dependency=current_user_av),
    session: AsyncSession = Depends(dependency=get_async_session),
):
    """Get all unread dialog events for the current user.

    Returns a list of dialog chat events with unread counts.

    Получает все непрочитанные события диалогов для текущего пользователя.

    Возвращает список событий диалоговых чатов с счётчиками непрочитанных.

    Args:
        user: The authenticated user.
        session: Async database session.

    Returns:
        List of dialog chat events.
    """
    stmt: Select = select(EventInDialogChat).where(
        EventInDialogChat.user_id == user.id
    )

    val: ChunkedIteratorResult = await session.execute(stmt)

    return ListItems[sc_EventInDialogChat](
        items=[sc_EventInDialogChat.model_validate(item) for item in val.scalars()]
    )


@events.get(
    path = '/groups/',
    response_model = ListItems[sc_EventInGroupChat]
)
async def get_groups_events(
    user: User = Depends(dependency=current_user_av),
    session: AsyncSession = Depends(dependency=get_async_session),
):
    """Get all unread group events for the current user.

    Returns a list of group chat events with unread counts.

    Получает все непрочитанные события групп для текущего пользователя.

    Возвращает список событий групповых чатов с счётчиками непрочитанных.

    Args:
        user: The authenticated user.
        session: Async database session.

    Returns:
        List of group chat events.
    """
    stmt: Select = select(EventInGroupChat).where(
        EventInGroupChat.user_id == user.id
    )

    val: ChunkedIteratorResult = await session.execute(stmt)

    return ListItems[sc_EventInGroupChat](
        items=[sc_EventInGroupChat.model_validate(item) for item in val.scalars()]
    )


@events.post(
    path = '/dialog/readed/{event_id}'
)
async def mark_readed_dialog(
    event_id: UUID,
    user: User = Depends(dependency=current_user_av),
    session: AsyncSession = Depends(dependency=get_async_session),
):
    """Mark a dialog event as read by resetting its counter to zero.

    Отмечает событие диалога как прочитанное, сбрасывая счётчик до нуля.

    Args:
        event_id: The event ID to mark as read.
        user: The authenticated user.
        session: Async database session.

    Raises:
        HTTPException: 404 if event not found or access denied.

    Returns:
        HTML response with 200 status.
    """
    try:

        event: EventInDialogChat = await session.get_one(
            entity = EventInDialogChat,
            ident = event_id
        )

        if event.user_id != user.id:
            raise NoResultFound

    except NoResultFound:

        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    event.count = 0

    await session.commit()

    return responses.HTMLResponse(
        status_code = status.HTTP_200_OK
    )


@events.post(
    path = '/group/readed/{event_id}'
)
async def mark_readed_group(
    event_id: UUID,
    user: User = Depends(dependency=current_user_av),
    session: AsyncSession = Depends(dependency=get_async_session),
):
    """Mark a group event as read by resetting its counter to zero.

    Отмечает событие группы как прочитанное, сбрасывая счётчик до нуля.

    Args:
        event_id: The event ID to mark as read.
        user: The authenticated user.
        session: Async database session.

    Raises:
        HTTPException: 404 if event not found or access denied.

    Returns:
        HTML response with 200 status.
    """
    try:

        event: EventInGroupChat = await session.get_one(
            entity = EventInGroupChat,
            ident = event_id
        )

        if event.user_id != user.id:
            raise NoResultFound

    except NoResultFound:

        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    event.count = 0

    await session.commit()

    return responses.HTMLResponse(
        status_code = status.HTTP_200_OK
    )

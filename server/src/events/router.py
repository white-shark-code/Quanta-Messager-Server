from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, responses, status
from sqlalchemy import ChunkedIteratorResult, Select, select
from sqlalchemy.exc import NoResultFound

from authentication.models import User
from authentication.services import current_user_av
from database import AsyncSession, get_async_session
from messages.schemas import ListItems

from .models import EventInDialogChat, EventInGroupChat
from .schemas import EventInChat as sc_EventInChat, EventInDialogChat as sc_EventInDialogChat, EventInGroupChat as sc_EventInGroupChat

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

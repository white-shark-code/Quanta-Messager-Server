from uuid import UUID

from sqlalchemy import ChunkedIteratorResult, Select, select
from sqlalchemy.exc import NoResultFound

from database import AsyncSession

from .models import EventInDialogChat


async def add_event_in_dialog_chat(
    session: AsyncSession,
    chat_id: UUID,
    user_id: UUID
):
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

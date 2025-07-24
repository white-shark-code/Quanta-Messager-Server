from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import (
    ChunkedIteratorResult,
    CompoundSelect,
    Select,
    select,
    union_all,
)
from sqlalchemy.exc import NoResultFound

from authentication.models import User
from authentication.services import current_user_av
from database import AsyncSession, get_async_session
from events.services import add_event_in_dialog_chat
from service.router_service import paggination

from .models import DialogChat, DialogMessage
from .schemas import (
    CreateDialogChat,
    CreateMessage,
    ListItems,
)
from .schemas import (
    DialogChat as sc_DialogChat,
)
from .schemas import (
    DialogMessage as sc_DialogMessage,
)
from .services import chech_signature_and_encryption

private_chats: APIRouter = APIRouter(prefix='/private-chat')
private_messages: APIRouter = APIRouter(prefix='/private-message')

@private_chats.get(path='/{chat_id}/', response_model=sc_DialogChat)
async def get_chat_info(
    chat_id: UUID,
    user: User = Depends(dependency=current_user_av),
    session: AsyncSession = Depends(dependency=get_async_session),
):
    try:
        dchat = await session.get_one(entity=DialogChat, ident=chat_id)
        if user.id not in [dchat.user0, dchat.user1]:
            raise NoResultFound
    except NoResultFound:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    return dchat

@private_chats.post(path='/', response_model=sc_DialogChat)
async def create_chat(
    new_chat: CreateDialogChat,
    user: User = Depends(dependency=current_user_av),
    session: AsyncSession = Depends(dependency=get_async_session),
):
    try:
        user1 = await session.get_one(entity=User, ident=new_chat.user)
    except NoResultFound:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    new_dialog_chat = DialogChat(user0=user.id, user1=user1.id, name=new_chat.name)

    session.add(new_dialog_chat)

    await session.commit()

    await session.refresh(new_dialog_chat)

    return new_dialog_chat

@private_chats.get(path='s/', response_model=ListItems[sc_DialogChat])
async def get_all_chats(
    pagginate: dict[str, int] = Depends(dependency=paggination),
    user: User = Depends(dependency=current_user_av),
    session: AsyncSession = Depends(dependency=get_async_session)
):
    user0_select: Select = select(DialogChat).where(DialogChat.user0 == user.id)
    user1_select: Select = select(DialogChat).where(DialogChat.user1 == user.id)
    union_select: CompoundSelect = \
        union_all(user0_select, user1_select)

    stmt: CompoundSelect = union_select

    val: ChunkedIteratorResult = await session.execute(stmt)

    return ListItems[sc_DialogChat](
        items=[sc_DialogChat.model_validate(item) for item in val.fetchall()]
    )

@private_chats.delete(path='/{chat_id}/', response_model=sc_DialogChat)
async def delete_chat(
    chat_id: UUID,
    user: User = Depends(dependency=current_user_av),
    session: AsyncSession = Depends(dependency=get_async_session),
):
    try:
        dchat = await session.get_one(entity=DialogChat, ident=chat_id)
        if user.id not in [dchat.user0, dchat.user1]:
            raise NoResultFound
    except NoResultFound:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    await session.delete(dchat)

    await session.commit()

    return dchat

@private_messages.get(path='s/{chat_id}', response_model=ListItems[sc_DialogMessage])
async def get_all_messages_from_chat(
    chat_id: UUID,
    pagginate: dict[str, int] = Depends(dependency=paggination),
    user: User = Depends(dependency=current_user_av),
    session: AsyncSession = Depends(dependency=get_async_session)
):
    try:
        dchat = await session.get_one(entity=DialogChat, ident=chat_id)
        if user.id not in [dchat.user0, dchat.user1]:
            raise NoResultFound
    except NoResultFound:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    main_select_stmt: Select = select(DialogMessage).where(
        DialogMessage.chat_id == dchat.id
    ).offset(pagginate['offset']).limit(pagginate['limit'])

    dialog_cursor: ChunkedIteratorResult = await session.execute(main_select_stmt)

    return ListItems[sc_DialogMessage](
        items=[
            sc_DialogMessage.model_validate(item)
            for item in dialog_cursor.scalars()
        ]
    )

@private_messages.post(path='/{chat_id}', response_model=sc_DialogMessage)
async def create_message(
    chat_id: UUID,
    new_message: CreateMessage,
    user: User = Depends(dependency=current_user_av),
    session: AsyncSession = Depends(dependency=get_async_session)
):
    if not user.public_key:
        raise HTTPException(
            status_code=status.HTTP_405_METHOD_NOT_ALLOWED,
            detail='Need add public key'
        )

    chech_signature_and_encryption(
        bytes_message = new_message.encrypted_message,
        bytes_signature = new_message.signature,
        bytes_public_key = user.public_key
    )

    try:
        dchat: DialogChat = await session.get_one(
            entity=DialogChat,
            ident=chat_id
        )

        if user.id not in [dchat.user0, dchat.user1]:
            raise NoResultFound
    except NoResultFound:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Chat not exist'
        )

    message_obj = DialogMessage(
        owner_id = user.id,
        encrypted_message = new_message.encrypted_message,
        chat_id = dchat.id
    )

    session.add(message_obj)

    if user.id != dchat.user0:
        await add_event_in_dialog_chat(
            session = session,
            chat_id = dchat.id,
            user_id = dchat.user0
        )
    else:
        await add_event_in_dialog_chat(
            session = session,
            chat_id = dchat.id,
            user_id = dchat.user1
        )

    await session.commit()

    await session.refresh(message_obj)

    return message_obj

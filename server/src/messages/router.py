"""API router for private and group chat and message endpoints.

API-маршруты для конечных точек приватных и групповых чатов и сообщений.
"""
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import (
    ChunkedIteratorResult,
    Select,
    select,
)
from sqlalchemy.exc import NoResultFound

from authentication.models import User, UserGroup
from authentication.schemas import Roles
from authentication.services import current_user_av
from database import AsyncSession, get_async_session
from events.services import add_event_in_dialog_chat, add_event_in_group_chat
from service.router_service import paggination

from .facade import DialogFacade
from .models import DialogChat, DialogMessage, GroupChat, GroupMessage
from .repository import DialogChatRepo
from .schemas import (
    CreateMessage,
    DefaultDialogChat,
    DeleteDialogChat,
    GetDialogChat,
    ListItems,
    PostDialogChat,
)
from .schemas import (
    DialogMessage as sc_DialogMessage,
)
from .services import chech_signature_and_encryption

private_chats: APIRouter = APIRouter(prefix='/private-chat')
private_messages: APIRouter = APIRouter(prefix='/private-message')
group_chats: APIRouter = APIRouter(prefix='/group-chat')
group_messages: APIRouter = APIRouter(prefix='/group-message')


@private_chats.get(path='/{chat_id}', response_model=DefaultDialogChat)
async def get_chat_info(
    chat_id: UUID,
    user: User = Depends(dependency=current_user_av),
    session: AsyncSession = Depends(dependency=get_async_session),
):
    """Retrieve information about a specific private chat.

    Получает информацию о конкретном приватном чате.

    Args:
        chat_id: The unique identifier of the chat.
        user: The currently authenticated user.
        session: The database session.

    Returns:
        The chat information if the user has access.
    """
    facade = DialogFacade(repo_class=DialogChatRepo, user=user, session=session)
    return await facade.read(GetDialogChat(id=chat_id))


@private_chats.post(path='/', response_model=DefaultDialogChat)
async def create_chat(
    new_chat: PostDialogChat,
    user: User = Depends(dependency=current_user_av),
    session: AsyncSession = Depends(dependency=get_async_session),
):
    """Create a new private dialog chat.

    Создает новый приватный диалоговый чат.

    Args:
        new_chat: The chat creation data containing name and target user.
        user: The currently authenticated user.
        session: The database session.

    Returns:
        The created chat object.
    """
    facade = DialogFacade(repo_class=DialogChatRepo, user=user, session=session)
    return await facade.create(new_chat)


@private_chats.get(path='s/', response_model=ListItems[DefaultDialogChat])
async def get_all_chats(
    user: User = Depends(dependency=current_user_av),
    session: AsyncSession = Depends(dependency=get_async_session)
):
    """Retrieve all private chats for the current user.

    Получает все приватные чаты текущего пользователя.

    Args:
        user: The currently authenticated user.
        session: The database session.

    Returns:
        A list of all chats the user participates in.
    """
    facade = DialogFacade(repo_class=DialogChatRepo, user=user, session=session)
    return await facade.get_all_chats()


@private_chats.delete(path='/{chat_id}/', response_model=DefaultDialogChat)
async def delete_chat(
    chat_id: UUID,
    user: User = Depends(dependency=current_user_av),
    session: AsyncSession = Depends(dependency=get_async_session),
):
    """Delete a private dialog chat.

    Удаляет приватный диалоговый чат.

    Args:
        chat_id: The unique identifier of the chat to delete.
        user: The currently authenticated user.
        session: The database session.

    Returns:
        The deleted chat object.
    """
    facade = DialogFacade(repo_class=DialogChatRepo, user=user, session=session)
    return await facade.delete(DeleteDialogChat(id=chat_id))


@private_messages.get(path='s/{chat_id}', response_model=ListItems[sc_DialogMessage])
async def get_all_messages_from_chat(
    chat_id: UUID,
    pagginate: dict[str, int] = Depends(dependency=paggination),
    user: User = Depends(dependency=current_user_av),
    session: AsyncSession = Depends(dependency=get_async_session)
):
    """Retrieve all messages from a specific private chat with pagination.

    Получает все сообщения из конкретного приватного чата с пагинацией.

    Args:
        chat_id: The unique identifier of the chat.
        pagginate: Pagination parameters (offset and limit).
        user: The currently authenticated user.
        session: The database session.

    Returns:
        A list of messages from the chat.

    Raises:
        HTTPException: 404 if the chat does not exist or user is not a participant.
    """
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
    """Create a new encrypted message in a private chat.

    Создает новое зашифрованное сообщение в приватном чате.

    Args:
        chat_id: The unique identifier of the target chat.
        new_message: The encrypted message data with signature.
        user: The currently authenticated user.
        session: The database session.

    Returns:
        The created message object.

    Raises:
        HTTPException: 405 if user has no public key, 404 if chat not found.
    """
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


@group_chats.post(path='/', response_model=DefaultDialogChat)
async def create_group_chat(
    new_chat: PostDialogChat,
    user: User = Depends(dependency=current_user_av),
    session: AsyncSession = Depends(dependency=get_async_session),
):
    """Create a new group chat with the current user as admin.

    Создает новый групповой чат с текущим пользователем в роли администратора.

    Args:
        new_chat: The chat creation data containing the name.
        user: The currently authenticated user.
        session: The database session.

    Returns:
        The created group chat object.

    Raises:
        HTTPException: 405 if user has no public key.
    """
    # Для простоты, предположим,
    # что создание группового чата требует наличия публичного ключа
    if not user.public_key:
        raise HTTPException(
            status_code=status.HTTP_405_METHOD_NOT_ALLOWED,
            detail='Need add public key'
        )

    # Создаем групповой чат
    new_group_chat = GroupChat(
        name=new_chat.name,
        public_key=user.public_key
    )

    # Добавляем пользователя в группу
    user_group = UserGroup(
        user_id=user.id,
        group_chat_id=new_group_chat.id,
        role=Roles.ADMIN
    )

    session.add(new_group_chat)
    session.add(user_group)

    await session.commit()

    await session.refresh(new_group_chat)

    return new_group_chat


@group_messages.post(path='/{chat_id}', response_model=sc_DialogMessage)
async def create_group_message(
    chat_id: UUID,
    new_message: CreateMessage,
    user: User = Depends(dependency=current_user_av),
    session: AsyncSession = Depends(dependency=get_async_session)
):
    """Create a new encrypted message in a group chat.

    Создает новое зашифрованное сообщение в групповом чате.

    Args:
        chat_id: The unique identifier of the target group chat.
        new_message: The encrypted message data with signature.
        user: The currently authenticated user.
        session: The database session.

    Returns:
        The created message object.

    Raises:
        HTTPException: 405 if user has no public key, 404 if chat not found.
    """
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
        gchat: GroupChat = await session.get_one(
            entity=GroupChat,
            ident=chat_id
        )

        # Проверяем, что пользователь состоит в группе
        await session.get_one(
            entity=UserGroup,
            ident=(user.id, gchat.id)
        )
    except NoResultFound:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Chat not exist or user not in chat'
        )

    message_obj = GroupMessage(
        owner_id = user.id,
        encrypted_message = new_message.encrypted_message,
        chat_id = gchat.id
    )

    session.add(message_obj)

    # Создаем события для всех пользователей в группе кроме отправителя
    stmt: Select = select(UserGroup).where(UserGroup.group_chat_id == gchat.id)
    user_groups = await session.execute(stmt)

    for ug in user_groups.scalars():
        if ug.user_id != user.id:
            await add_event_in_group_chat(
                session = session,
                chat_id = gchat.id,
                user_id = ug.user_id
            )

    await session.commit()

    await session.refresh(message_obj)

    return message_obj

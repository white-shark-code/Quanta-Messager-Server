"""API router for private and group chat and message endpoints.

API-маршруты для конечных точек приватных и групповых чатов и сообщений.
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import (
    ChunkedIteratorResult,
    Select,
    select,
    update,
)
from sqlalchemy.exc import NoResultFound

from authentication.models import User, UserGroup
from authentication.schemas import Roles
from authentication.services import current_user_av
from database import AsyncSession, get_async_session
from events.services import add_event_in_dialog_chat, add_event_in_group_chat
from service.router_service import paggination
from settings import cfg

from .facade import DialogFacade
from .models import DialogChat, DialogMessage, GroupChat, GroupMessage, MediaAttachment
from .repository import DialogChatRepo
from .schemas import (
    CreateMessage,
    DefaultDialogChat,
    DeleteDialogChat,
    GetDialogChat,
    ListItems,
    MediaAttachmentDownload,
    MediaAttachmentResponse,
    PostDialogChat,
    UploadMediaAttachment,
)
from .schemas import (
    DialogMessage as sc_DialogMessage,
)
from .services import chech_signature_and_encryption, check_media_signature
from .storage import DatabaseMediaStorage

private_chats: APIRouter = APIRouter(prefix="/private-chat")
private_messages: APIRouter = APIRouter(prefix="/private-message")
group_chats: APIRouter = APIRouter(prefix="/group-chat")
group_messages: APIRouter = APIRouter(prefix="/group-message")


@private_chats.get(path="/{chat_id}", response_model=DefaultDialogChat)
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


@private_chats.post(path="/", response_model=DefaultDialogChat)
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


@private_chats.get(path="s/", response_model=ListItems[DefaultDialogChat])
async def get_all_chats(
    user: User = Depends(dependency=current_user_av),
    session: AsyncSession = Depends(dependency=get_async_session),
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


@private_chats.delete(path="/{chat_id}/", response_model=DefaultDialogChat)
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


@private_messages.get(path="s/{chat_id}", response_model=ListItems[sc_DialogMessage])
async def get_all_messages_from_chat(
    chat_id: UUID,
    pagginate: dict[str, int] = Depends(dependency=paggination),
    user: User = Depends(dependency=current_user_av),
    session: AsyncSession = Depends(dependency=get_async_session),
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

    main_select_stmt: Select = (
        select(DialogMessage)
        .where(DialogMessage.chat_id == dchat.id)
        .offset(pagginate["offset"])
        .limit(pagginate["limit"])
    )

    dialog_cursor: ChunkedIteratorResult = await session.execute(main_select_stmt)

    return ListItems[sc_DialogMessage](
        items=[
            sc_DialogMessage.model_validate(item) for item in dialog_cursor.scalars()
        ]
    )


@private_messages.post(path="/{chat_id}", response_model=sc_DialogMessage)
async def create_message(
    chat_id: UUID,
    new_message: CreateMessage,
    user: User = Depends(dependency=current_user_av),
    session: AsyncSession = Depends(dependency=get_async_session),
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
            status_code=status.HTTP_405_METHOD_NOT_ALLOWED, detail="Need add public key"
        )

    chech_signature_and_encryption(
        bytes_message=new_message.encrypted_message,
        bytes_signature=new_message.signature,
        bytes_public_key=user.public_key,
    )

    try:
        dchat: DialogChat = await session.get_one(entity=DialogChat, ident=chat_id)

        if user.id not in [dchat.user0, dchat.user1]:
            raise NoResultFound
    except NoResultFound:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Chat not exist"
        )

    message_obj = DialogMessage(
        owner_id=user.id,
        encrypted_message=new_message.encrypted_message,
        chat_id=dchat.id,
    )

    session.add(message_obj)

    if user.id != dchat.user0:
        await add_event_in_dialog_chat(
            session=session, chat_id=dchat.id, user_id=dchat.user0
        )
    else:
        await add_event_in_dialog_chat(
            session=session, chat_id=dchat.id, user_id=dchat.user1
        )

    if new_message.media_ids:
        stmt = (
            update(MediaAttachment)
            .where(
                MediaAttachment.id.in_(new_message.media_ids),
                MediaAttachment.owner_id == user.id,
                MediaAttachment.dialog_message_id.is_(None),
            )
            .values(dialog_message_id=message_obj.id)
        )
        await session.execute(stmt)

    await session.commit()

    await session.refresh(message_obj)

    return message_obj


@group_chats.post(path="/", response_model=DefaultDialogChat)
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
            status_code=status.HTTP_405_METHOD_NOT_ALLOWED, detail="Need add public key"
        )

    # Создаем групповой чат
    new_group_chat = GroupChat(name=new_chat.name, public_key=user.public_key)

    # Добавляем пользователя в группу
    user_group = UserGroup(
        user_id=user.id, group_chat_id=new_group_chat.id, role=Roles.ADMIN
    )

    session.add(new_group_chat)
    session.add(user_group)

    await session.commit()

    await session.refresh(new_group_chat)

    return new_group_chat


@group_messages.post(path="/{chat_id}", response_model=sc_DialogMessage)
async def create_group_message(
    chat_id: UUID,
    new_message: CreateMessage,
    user: User = Depends(dependency=current_user_av),
    session: AsyncSession = Depends(dependency=get_async_session),
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
            status_code=status.HTTP_405_METHOD_NOT_ALLOWED, detail="Need add public key"
        )

    chech_signature_and_encryption(
        bytes_message=new_message.encrypted_message,
        bytes_signature=new_message.signature,
        bytes_public_key=user.public_key,
    )

    try:
        gchat: GroupChat = await session.get_one(entity=GroupChat, ident=chat_id)

        # Проверяем, что пользователь состоит в группе
        await session.get_one(entity=UserGroup, ident=(user.id, gchat.id))
    except NoResultFound:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat not exist or user not in chat",
        )

    message_obj = GroupMessage(
        owner_id=user.id,
        encrypted_message=new_message.encrypted_message,
        chat_id=gchat.id,
    )

    session.add(message_obj)

    # Создаем события для всех пользователей в группе кроме отправителя
    stmt: Select = select(UserGroup).where(UserGroup.group_chat_id == gchat.id)
    user_groups = await session.execute(stmt)

    for ug in user_groups.scalars():
        if ug.user_id != user.id:
            await add_event_in_group_chat(
                session=session, chat_id=gchat.id, user_id=ug.user_id
            )

    if new_message.media_ids:
        media_stmt = (
            update(MediaAttachment)
            .where(
                MediaAttachment.id.in_(new_message.media_ids),
                MediaAttachment.owner_id == user.id,
                MediaAttachment.group_message_id.is_(None),
            )
            .values(group_message_id=message_obj.id)
        )
        await session.execute(media_stmt)

    await session.commit()

    await session.refresh(message_obj)

    return message_obj


# ------------------- Private Media Endpoints -------------------


@private_messages.post(
    path="/{chat_id}/media/upload",
    response_model=MediaAttachmentResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_private_media(
    chat_id: UUID,
    upload: UploadMediaAttachment,
    user: User = Depends(dependency=current_user_av),
    session: AsyncSession = Depends(dependency=get_async_session),
):
    """Upload encrypted media to a private chat.

    Загружает зашифрованное медиа в приватный чат.
    """
    if upload.file_size > cfg.MAX_MEDIA_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="File too large",
        )

    if not user.public_key:
        raise HTTPException(
            status_code=status.HTTP_405_METHOD_NOT_ALLOWED, detail="Need add public key"
        )

    check_media_signature(
        bytes_file=upload.encrypted_file,
        bytes_signature=upload.signature,
        bytes_public_key=user.public_key,
    )

    try:
        dchat = await session.get_one(entity=DialogChat, ident=chat_id)
        if user.id not in [dchat.user0, dchat.user1]:
            raise NoResultFound
    except NoResultFound:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    media = MediaAttachment(
        mime_type=upload.mime_type,
        file_size=upload.file_size,
        signature=upload.signature,
        owner_id=user.id,
    )
    session.add(media)
    await session.flush()

    storage = DatabaseMediaStorage()
    await storage.save(session, media.id, upload.encrypted_file)

    await session.commit()
    await session.refresh(media)
    return media


@private_messages.get(
    path="/{message_id}/media/",
    response_model=ListItems[MediaAttachmentResponse],
)
async def list_private_media(
    message_id: UUID,
    user: User = Depends(dependency=current_user_av),
    session: AsyncSession = Depends(dependency=get_async_session),
):
    """List media attachments for a private message.

    Получает список медиа-вложений для сообщения в приватном чате.
    """
    try:
        message = await session.get_one(entity=DialogMessage, ident=message_id)
        dchat = await session.get_one(entity=DialogChat, ident=message.chat_id)
        if user.id not in [dchat.user0, dchat.user1]:
            raise NoResultFound
    except NoResultFound:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    stmt = select(MediaAttachment).where(
        MediaAttachment.dialog_message_id == message_id
    )
    result = await session.execute(stmt)
    items = result.scalars()

    return ListItems[MediaAttachmentResponse](
        items=[MediaAttachmentResponse.model_validate(item) for item in items]
    )


@private_messages.get(path="/media/{media_id}", response_model=MediaAttachmentDownload)
async def download_private_media(
    media_id: UUID,
    user: User = Depends(dependency=current_user_av),
    session: AsyncSession = Depends(dependency=get_async_session),
):
    """Download encrypted media from a private chat.

    Скачивает зашифрованное медиа из приватного чата.
    """
    try:
        media = await session.get_one(entity=MediaAttachment, ident=media_id)
    except NoResultFound:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    if media.dialog_message_id:
        message = await session.get_one(
            entity=DialogMessage, ident=media.dialog_message_id
        )
        dchat = await session.get_one(entity=DialogChat, ident=message.chat_id)
        if user.id not in [dchat.user0, dchat.user1]:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)

    encrypted_file = await DatabaseMediaStorage().load(session, media.id)

    download = MediaAttachmentDownload(
        id=media.id,
        mime_type=media.mime_type,
        file_size=media.file_size,
        owner_id=media.owner_id,
        creation_datetime=media.creation_datetime,
        encrypted_file=encrypted_file,
        signature=media.signature,
    )
    return download


@private_messages.delete(
    path="/media/{media_id}/",
    response_model=MediaAttachmentResponse,
)
async def delete_private_media(
    media_id: UUID,
    user: User = Depends(dependency=current_user_av),
    session: AsyncSession = Depends(dependency=get_async_session),
):
    """Delete media from a private chat.

    Удаляет медиа-вложение из приватного чата.
    """
    try:
        media = await session.get_one(entity=MediaAttachment, ident=media_id)
    except NoResultFound:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    if media.owner_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)

    if media.dialog_message_id is not None:
        media.dialog_message_id = None

    await DatabaseMediaStorage().delete(session, media.id)
    await session.delete(media)
    await session.commit()

    return MediaAttachmentResponse(
        id=media.id,
        mime_type=media.mime_type,
        file_size=media.file_size,
        creation_datetime=media.creation_datetime,
    )


# ------------------- Group Media Endpoints -------------------


@group_messages.post(
    path="/{chat_id}/media/upload",
    response_model=MediaAttachmentResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_group_media(
    chat_id: UUID,
    upload: UploadMediaAttachment,
    user: User = Depends(dependency=current_user_av),
    session: AsyncSession = Depends(dependency=get_async_session),
):
    """Upload encrypted media to a group chat.

    Загружает зашифрованное медиа в групповой чат.
    """
    if upload.file_size > cfg.MAX_MEDIA_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="File too large",
        )

    if not user.public_key:
        raise HTTPException(
            status_code=status.HTTP_405_METHOD_NOT_ALLOWED, detail="Need add public key"
        )

    check_media_signature(
        bytes_file=upload.encrypted_file,
        bytes_signature=upload.signature,
        bytes_public_key=user.public_key,
    )

    try:
        gchat = await session.get_one(entity=GroupChat, ident=chat_id)
        await session.get_one(entity=UserGroup, ident=(user.id, gchat.id))
    except NoResultFound:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    media = MediaAttachment(
        mime_type=upload.mime_type,
        file_size=upload.file_size,
        signature=upload.signature,
        owner_id=user.id,
    )
    session.add(media)
    await session.flush()

    storage = DatabaseMediaStorage()
    await storage.save(session, media.id, upload.encrypted_file)

    await session.commit()
    await session.refresh(media)
    return media


@group_messages.get(
    path="/{message_id}/media/",
    response_model=ListItems[MediaAttachmentResponse],
)
async def list_group_media(
    message_id: UUID,
    user: User = Depends(dependency=current_user_av),
    session: AsyncSession = Depends(dependency=get_async_session),
):
    """List media attachments for a group message.

    Получает список медиа-вложений для сообщения в групповом чате.
    """
    try:
        message = await session.get_one(entity=GroupMessage, ident=message_id)
        gchat = await session.get_one(entity=GroupChat, ident=message.chat_id)
        await session.get_one(entity=UserGroup, ident=(user.id, gchat.id))
    except NoResultFound:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    stmt = select(MediaAttachment).where(MediaAttachment.group_message_id == message_id)
    result = await session.execute(stmt)
    items = result.scalars()

    return ListItems[MediaAttachmentResponse](
        items=[MediaAttachmentResponse.model_validate(item) for item in items]
    )


@group_messages.get(path="/media/{media_id}", response_model=MediaAttachmentDownload)
async def download_group_media(
    media_id: UUID,
    user: User = Depends(dependency=current_user_av),
    session: AsyncSession = Depends(dependency=get_async_session),
):
    """Download encrypted media from a group chat.

    Скачивает зашифрованное медиа из группового чата.
    """
    try:
        media = await session.get_one(entity=MediaAttachment, ident=media_id)
    except NoResultFound:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    if media.group_message_id:
        message = await session.get_one(
            entity=GroupMessage, ident=media.group_message_id
        )
        gchat = await session.get_one(entity=GroupChat, ident=message.chat_id)
        try:
            await session.get_one(entity=UserGroup, ident=(user.id, gchat.id))
        except NoResultFound:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)

    encrypted_file = await DatabaseMediaStorage().load(session, media.id)

    download = MediaAttachmentDownload(
        id=media.id,
        mime_type=media.mime_type,
        file_size=media.file_size,
        owner_id=media.owner_id,
        creation_datetime=media.creation_datetime,
        encrypted_file=encrypted_file,
        signature=media.signature,
    )
    return download


@group_messages.delete(
    path="/media/{media_id}/",
    response_model=MediaAttachmentResponse,
)
async def delete_group_media(
    media_id: UUID,
    user: User = Depends(dependency=current_user_av),
    session: AsyncSession = Depends(dependency=get_async_session),
):
    """Delete media from a group chat.

    Удаляет медиа-вложение из группового чата.
    """
    try:
        media = await session.get_one(entity=MediaAttachment, ident=media_id)
    except NoResultFound:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    if media.owner_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)

    if media.group_message_id is not None:
        media.group_message_id = None

    await DatabaseMediaStorage().delete(session, media.id)
    await session.delete(media)
    await session.commit()

    return MediaAttachmentResponse(
        id=media.id,
        mime_type=media.mime_type,
        file_size=media.file_size,
        creation_datetime=media.creation_datetime,
    )

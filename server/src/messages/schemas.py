"""Pydantic schemas for messaging system request/response validation.

Pydantic-схемы для валидации запросов и ответов системы сообщений.
"""

from datetime import datetime
from typing import Generic, TypeVar
from uuid import UUID

from pydantic import Base64Bytes, BaseModel, ConfigDict

from shared.abstract_schemas import AbstractUUIDPagginationBaseModel
from shared.basic_schemas import UUIDGetPagginationBaseModel


class UploadMediaAttachment(BaseModel):
    """Schema for uploading an encrypted media attachment with signature.

    Схема для загрузки зашифрованного медиаприложения с подписью.
    """

    encrypted_file: Base64Bytes
    signature: Base64Bytes
    mime_type: str
    file_size: int


class MediaAttachmentResponse(BaseModel):
    """Response schema for a media attachment.

    Схема ответа для медиаприложения.
    """

    id: UUID
    mime_type: str
    file_size: int
    creation_datetime: datetime

    model_config = ConfigDict(from_attributes=True)


class MediaAttachmentDownload(BaseModel):
    """Schema for downloading a media attachment with encrypted file and signature.

    Схема для скачивания медиаприложения с зашифрованным файлом и подписью.
    """

    id: UUID
    mime_type: str
    file_size: int
    encrypted_file: bytes
    signature: bytes
    owner_id: UUID
    creation_datetime: datetime

    model_config = ConfigDict(from_attributes=True)


class GetChat(BaseModel):
    """Base schema for retrieving a chat by ID.

    Базовая схема для получения чата по идентификатору.
    """

    model_config = ConfigDict(from_attributes=True)

    id: UUID


class Chat(GetChat):
    """Base schema for chat with name.

    Базовая схема для чата с именем.
    """

    name: str


class DefaultDialogChat(Chat):
    """Complete dialog chat schema with all fields.

    Полная схема диалога со всеми полями.
    """

    model_config = ConfigDict(from_attributes=True)

    user0: UUID
    user1: UUID
    create_at: datetime


class PostDialogChat(BaseModel):
    """Schema for creating a new dialog chat.

    Схема для создания нового диалога.
    """

    name: str
    user: UUID


class GetDialogChat(GetChat):
    """Schema for retrieving a dialog chat.

    Схема для получения диалога.
    """

    pass


class PatchDialogChat(Chat):
    """Schema for updating a dialog chat.

    Схема для обновления диалога.
    """

    pass


class DeleteDialogChat(GetDialogChat):
    """Schema for deleting a dialog chat.

    Схема для удаления диалога.
    """

    pass


class PagginationDialogChats(AbstractUUIDPagginationBaseModel[DefaultDialogChat]):
    """Paginated response schema for dialog chats.

    Схема пагинированного ответа для диалогов.
    """

    pass


class DefaultGroupChat(Chat):
    """Group chat output schema with metadata.

    Выходная схема группового чата с метаданными.
    """

    model_config = ConfigDict(from_attributes=True)

    public_key: bytes
    create_at: datetime


class PostGroupChat(BaseModel):
    """Schema for creating a new group chat.

    Схема для создания нового группового чата.
    """

    name: str
    public_key: bytes


class GetGroupChat(GetChat):
    """Schema for retrieving a group chat.

    Схема для получения группового чата.
    """

    pass


class DeleteGroupChat(GetGroupChat):
    """Schema for deleting a group chat.

    Схема для удаления группового чата.
    """

    pass


class PagginationGroupChats(AbstractUUIDPagginationBaseModel[DefaultGroupChat]):
    """Paginated response schema for group chats.

    Схема пагинированного ответа для групповых чатов.
    """

    pass


class EncryptedText(BaseModel):
    """Base schema for encrypted message content (response/storage side).

    The raw bytes are stored as-is; FastAPI's ``jsonable_encoder``
    base64-encodes them for JSON output transparently.

    `signature` is the detached PGP signature over the ciphertext —
    stored as bytes and base64-encoded by the response layer. Nullable
    so messages written before the column was added round-trip cleanly.

    Базовая схема зашифрованного содержимого (response-сторона).
    """

    encrypted_message: bytes
    signature: bytes | None = None


class EncryptedTextRequest(BaseModel):
    """Request-side base for encrypted message payloads.

    Fields are base64-encoded on the wire: clients send base64 strings,
    Pydantic decodes them back to raw PGP armored bytes for the
    server to verify.

    Request-база для зашифрованных сообщений: клиент шлёт base64,
    pydantic декодирует в исходные PGP armored bytes.
    """

    encrypted_message: Base64Bytes


class CreateMessage(EncryptedTextRequest):
    """Schema for creating a new encrypted message with signature.

    Схема для создания нового зашифрованного сообщения с подписью.
    """

    signature: Base64Bytes
    media_ids: list[UUID] | None = None


class Message(EncryptedText):
    """Base message schema with owner and timestamp.

    Базовая схема сообщения с владельцем и временной меткой.
    """

    model_config = ConfigDict(from_attributes=True)

    owner_id: UUID
    creation_datetime: datetime


class DefaultMessage(Message):
    """Default complete message schema.

    Полная схема сообщения по умолчанию.
    """

    pass


class GetDialogMessage(BaseModel):
    """Schema for retrieving a dialog message.

    Схема для получения сообщения диалога.
    """

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    chat_id: UUID


class DialogMessage(Message):
    """Message schema with chat reference.

    Схема сообщения со ссылкой на чат.
    """

    id: UUID
    chat_id: UUID


class DefaultDialogMessage(DefaultMessage):
    """Default dialog message schema with explicit ID.

    Полная схема сообщения диалога с явным идентификатором.
    """

    id: UUID


class PostDialogMessage(CreateMessage, DialogMessage):
    """Schema for creating a new dialog message.

    Схема для создания нового сообщения диалога.
    """

    pass


class PagginationMessage(AbstractUUIDPagginationBaseModel[DefaultMessage]):
    """Paginated response schema for messages.

    Схема пагинированного ответа для сообщений.
    """

    pass


class GetPagginationDialogMessage(UUIDGetPagginationBaseModel):
    """Pagination request schema for dialog messages.

    Схема пагинационного запроса для сообщений диалога.
    """

    chat_id: UUID


class PagginationDialogMessage(PagginationMessage):
    """Paginated response schema for dialog messages with chat reference.

    Схема пагинированного ответа для сообщений диалога со ссылкой на чат.
    """

    chat_id: UUID


class GroupMessage(Message):
    """Schema for group messages with chat reference.

    Схема группового сообщения со ссылкой на чат.
    """

    model_config = ConfigDict(from_attributes=True)

    chat_id: UUID


V: TypeVar = TypeVar("V")


class ListItems(BaseModel, Generic[V]):
    """Generic container for a list of items.

    Универсальный контейнер для списка элементов.
    """

    items: list[V]

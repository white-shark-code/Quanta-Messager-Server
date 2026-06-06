"""Pydantic schemas for messaging system request/response validation.

Pydantic-схемы для валидации запросов и ответов системы сообщений.
"""
from datetime import datetime
from typing import Generic, TypeVar
from uuid import UUID

from pydantic import BaseModel

from shared.abstract_schemas import AbstractUUIDPagginationBaseModel
from shared.basic_schemas import UUIDGetPagginationBaseModel


class GetChat(BaseModel):
    """Base schema for retrieving a chat by ID.

    Базовая схема для получения чата по идентификатору.
    """
    id: UUID

    class Config:
        from_attributes = True


class Chat(GetChat):
    """Base schema for chat with name.

    Базовая схема для чата с именем.
    """
    name: str


class DefaultDialogChat(Chat):
    """Complete dialog chat schema with all fields.

    Полная схема диалога со всеми полями.
    """
    user0: UUID
    user1: UUID
    creation_datetime: datetime

    class Config:
        from_attributes = True


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


class PagginationDialogChats(
    AbstractUUIDPagginationBaseModel[
        DefaultDialogChat
    ]
):
    """Paginated response schema for dialog chats.

    Схема пагинированного ответа для диалогов.
    """
    pass


class GroupChat(Chat):
    """Schema for group chat with users and public key.

    Схема группового чата с пользователями и публичным ключом.
    """
    users: UUID
    creation_datetime: datetime
    public_key: bytes

    class Config:
        from_attributes = True


class EncryptedText(BaseModel):
    """Base schema for encrypted message content.

    Базовая схема для зашифрованного содержимого сообщения.
    """
    encrypted_message: bytes


class CreateMessage(EncryptedText):
    """Schema for creating a new encrypted message with signature.

    Схема для создания нового зашифрованного сообщения с подписью.
    """
    signature: bytes


class Message(EncryptedText):
    """Base message schema with owner and timestamp.

    Базовая схема сообщения с владельцем и временной меткой.
    """
    owner_id: UUID
    creation_datetime: datetime

    class Config:
        from_attributes = True


class DefaultMessage(
    Message
):
    """Default complete message schema.

    Полная схема сообщения по умолчанию.
    """
    pass


class GetDialogMessage(BaseModel):
    """Schema for retrieving a dialog message.

    Схема для получения сообщения диалога.
    """
    id: UUID
    chat_id: UUID

    class Config:
        from_attributes = True


class DialogMessage(Message):
    """Message schema with chat reference.

    Схема сообщения со ссылкой на чат.
    """
    chat_id: UUID


class DefaultDialogMessage(
    DefaultMessage
):
    """Default dialog message schema with explicit ID.

    Полная схема сообщения диалога с явным идентификатором.
    """
    id: UUID


class PostDialogMessage(
    CreateMessage,
    DialogMessage
):
    """Schema for creating a new dialog message.

    Схема для создания нового сообщения диалога.
    """
    pass


class PagginationMessage(
    AbstractUUIDPagginationBaseModel[
        DefaultMessage
    ]
):
    """Paginated response schema for messages.

    Схема пагинированного ответа для сообщений.
    """
    pass


class GetPagginationDialogMessage(
    UUIDGetPagginationBaseModel
):
    """Pagination request schema for dialog messages.

    Схема пагинационного запроса для сообщений диалога.
    """
    chat_id: UUID


class PagginationDialogMessage(
    PagginationMessage
):
    """Paginated response schema for dialog messages with chat reference.

    Схема пагинированного ответа для сообщений диалога со ссылкой на чат.
    """
    chat_id: UUID


class GroupMessage(Message):
    """Schema for group messages with chat reference.

    Схема группового сообщения со ссылкой на чат.
    """
    chat_id: UUID

    class Config:
        from_attributes = True


V: TypeVar = TypeVar('V')


class ListItems(BaseModel, Generic[V]):
    """Generic container for a list of items.

    Универсальный контейнер для списка элементов.
    """
    items: list[V]

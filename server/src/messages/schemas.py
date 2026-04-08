from datetime import datetime
from typing import Generic, TypeVar
from pydantic import BaseModel
from uuid import UUID
from shared.abstract_schemas import (
    AbstractUUIDPagginationBaseModel
)


class GetChat(BaseModel):
    id: UUID

    class Config:
        from_attributes = True


class Chat(GetChat):
    name: str


class DefaultDialogChat(Chat):
    user0: UUID
    user1: UUID
    creation_datetime: datetime

    class Config:
        from_attributes = True


class PostDialogChat(BaseModel):
    name: str
    user: UUID


class GetDialogChat(GetChat):
    pass


class PatchDialogChat(Chat):
    pass


class DeleteDialogChat(GetDialogChat):
    pass


class PagginationDialogChats(
    AbstractUUIDPagginationBaseModel[
        DefaultDialogChat
    ]
):
    pass

class GroupChat(Chat):
    users: UUID
    creation_datetime: datetime
    public_key: bytes

    class Config:
        from_attributes = True


class EncryptedText(BaseModel):
    encrypted_message: bytes


class CreateMessage(EncryptedText):
    signature: bytes


class Message(EncryptedText):
    id: UUID
    owner_id: UUID
    creation_datetime: datetime

    class Config:
        from_attributes = True


class DialogMessage(Message):
    chat_id: UUID

    class Config:
        from_attributes = True


class GroupMessage(Message):
    chat_id: UUID

    class Config:
        from_attributes = True


V: TypeVar = TypeVar('V')

class ListItems(BaseModel, Generic[V]):
    items: list[V]

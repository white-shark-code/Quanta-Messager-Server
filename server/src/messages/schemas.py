from datetime import datetime
from typing import Generic, TypeVar
from uuid import UUID

from pydantic import BaseModel


class Chat(BaseModel):
    id: UUID
    name: str

    class Config:
        from_attributes = True


class DialogChat(Chat):
    user0: UUID
    user1: UUID
    creation_datetime: datetime

    class Config:
        from_attributes = True


class CreateDialogChat(BaseModel):
    name: str
    user: UUID


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

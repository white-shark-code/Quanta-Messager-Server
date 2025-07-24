from uuid import UUID

from pydantic import BaseModel


class EventInChat(BaseModel):
    id: UUID
    chat_id: UUID
    user_id: UUID
    count: int

    class Config:
        from_attributes = True

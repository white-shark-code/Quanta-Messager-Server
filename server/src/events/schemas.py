"""Event schemas for API request/response validation.

This module defines Pydantic schemas for serializing event data
returned by the events API endpoints.

Схемы событий для валидации запросов/ответов API.

Модуль определяет Pydantic-схемы для сериализации данных событий,
возвращаемых эндпоинтами API событий.
"""

from uuid import UUID

from pydantic import BaseModel


class EventInChat(BaseModel):
    """Base event schema for chat events.

    Базовая схема события в чате.
    """
    id: UUID
    chat_id: UUID
    user_id: UUID
    count: int

    class Config:
        from_attributes = True


class EventInDialogChat(EventInChat):
    """Dialog chat event schema.

    Схема события в диалоговом чате.
    """
    pass


class EventInGroupChat(EventInChat):
    """Group chat event schema.

    Схема события в групповом чате.
    """
    pass

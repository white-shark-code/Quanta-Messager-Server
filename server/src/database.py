"""Database configuration and session management.

This module provides SQLAlchemy engine and session factories
for asynchronous database operations.

Конфигурация базы данных и управление сессиями.

Модуль предоставляет фабрики движков и сессий SQLAlchemy
для асинхронных операций с базой данных.
"""

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from settings import cfg


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy declarative models.

    Базовый класс для всех SQLAlchemy декларативных моделей.
    """

    pass


_async_engine: AsyncEngine | None = None
_async_session_maker: async_sessionmaker | None = None


def _get_engine() -> AsyncEngine:
    """Lazily create async engine on first access.

    Лениво создаёт async engine при первом обращении.
    """
    global _async_engine, _async_session_maker
    if _async_engine is None:
        _async_engine = create_async_engine(url=cfg.DATABASE_URL)
        _async_session_maker = async_sessionmaker(
            bind=_async_engine, expire_on_commit=False
        )
    return _async_engine


def _get_session_maker() -> async_sessionmaker:
    """Return session maker, initializing engine if needed.

    Возвращает session maker, инициализируя engine при необходимости.
    """
    _get_engine()
    assert _async_session_maker is not None
    return _async_session_maker


async def get_async_session() -> AsyncGenerator[AsyncSession]:
    """Dependency generator for asynchronous database sessions.

    Генератор зависимости для асинхронных сессий базы данных.

    Yields:
        Async SQLAlchemy Session instance.
    """
    async with _get_session_maker()() as session:
        yield session

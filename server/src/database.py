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


async_engine: AsyncEngine = create_async_engine(url=cfg.DATABASE_URL)
async_session_maker: async_sessionmaker = async_sessionmaker(
    bind=async_engine, expire_on_commit=False
)


async def get_async_session() -> AsyncGenerator[AsyncSession]:
    """Dependency generator for asynchronous database sessions.

    Генератор зависимости для асинхронных сессий базы данных.

    Yields:
        Async SQLAlchemy Session instance.
    """
    async with async_session_maker() as session:
        yield session

"""Database configuration and session management.

This module provides SQLAlchemy engine and session factories
for both synchronous and asynchronous database operations.

Конфигурация базы данных и управление сессиями.

Модуль предоставляет фабрики движков и сессий SQLAlchemy
для синхронных и асинхронных операций с базой данных.
"""

from collections.abc import AsyncGenerator, Generator

from sqlalchemy.engine import Engine, create_engine
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from settings import cfg


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy declarative models.

    Базовый класс для всех SQLAlchemy декларативных моделей.
    """
    pass


sync_engine: Engine = create_engine(url=cfg.DATABASE_URL)
sync_session_maker: sessionmaker = sessionmaker(
    bind=sync_engine,
    expire_on_commit=False
)

async_engine: AsyncEngine = create_async_engine(url=cfg.DATABASE_URL)
async_session_maker: async_sessionmaker = async_sessionmaker(
    bind=async_engine,
    expire_on_commit=False
)


def get_sync_session() -> Generator[Session]:
    """Dependency generator for synchronous database sessions.

    Генератор зависимости для синхронных сессий базы данных.

    Yields:
        SQLAlchemy Session instance.
    """
    with sync_session_maker() as session:
        yield session


async def get_async_session() -> AsyncGenerator[AsyncSession]:
    """Dependency generator for asynchronous database sessions.

    Генератор зависимости для асинхронных сессий базы данных.

    Yields:
        Async SQLAlchemy Session instance.
    """
    async with async_session_maker() as session:
        yield session

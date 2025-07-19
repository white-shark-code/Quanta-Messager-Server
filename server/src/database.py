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
    with sync_session_maker as session:
        yield session

async def get_async_session() -> AsyncGenerator[AsyncSession]:
    async with async_session_maker() as session:
        yield session

"""Media storage abstraction for encrypted file blobs.

Абстракция хранилища для зашифрованных медиа-блобов.
"""

from abc import ABC, abstractmethod
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .models import MediaBlobData


class MediaStorage(ABC):
    """Abstract base class for media storage backends.

    Абстрактный базовый класс для бэкендов хранения медиа.
    """

    @abstractmethod
    async def save(self, session: AsyncSession, media_id: UUID, data: bytes) -> None:
        """Save encrypted media blob data.

        Сохраняет данные зашифрованного медиа-блоба.
        """
        ...

    @abstractmethod
    async def load(self, session: AsyncSession, media_id: UUID) -> bytes:
        """Load encrypted media blob data.

        Загружает данные зашифрованного медиа-блоба.
        """
        ...

    @abstractmethod
    async def delete(self, session: AsyncSession, media_id: UUID) -> None:
        """Delete encrypted media blob data.

        Удаляет данные зашифрованного медиа-блоба.
        """
        ...


class DatabaseMediaStorage(MediaStorage):
    """Media storage implementation using the database.

    Реализация хранения медиа через базу данных.
    """

    async def save(self, session: AsyncSession, media_id: UUID, data: bytes) -> None:
        """Save encrypted media blob to the database.

        Сохраняет зашифрованный медиа-блоб в базу данных.
        """
        blob = MediaBlobData(media_id=media_id, encrypted_file=data)
        session.add(blob)

    async def load(self, session: AsyncSession, media_id: UUID) -> bytes:
        """Load encrypted media blob from the database.

        Загружает зашифрованный медиа-блоб из базы данных.
        """
        result = await session.execute(
            select(MediaBlobData).where(MediaBlobData.media_id == media_id)
        )
        blob = result.scalar_one()
        return blob.encrypted_file

    async def delete(self, session: AsyncSession, media_id: UUID) -> None:
        """Delete encrypted media blob from the database.

        Удаляет зашифрованный медиа-блоб из базы данных.
        """
        blob = await session.execute(
            select(MediaBlobData).where(MediaBlobData.media_id == media_id)
        )
        result = blob.scalar_one_or_none()
        if result:
            await session.delete(result)

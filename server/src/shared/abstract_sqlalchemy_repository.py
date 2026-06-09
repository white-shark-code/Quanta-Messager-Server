"""Abstract SQLAlchemy repository base class.

This module provides the base repository class for SQLAlchemy-based
data access with async session management and user context.

Базовый класс SQLAlchemy-репозитория.

Модуль предоставляет базовый класс репозитория для доступа к данным
через SQLAlchemy с асинхронным управлением сессиями и контекстом пользователя.
"""

from abc import ABC, abstractmethod
from typing import Generic, TypeVar

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import Select

from authentication.models import User
from database import Base

from .abstract_repository import (
    AbstractDefaultPydanticModel,
    AbstractID,
)
from .abstract_sqlalchemy_models import AbstractModelWithIntID, AbstractModelWithUUID

AbstractSQLAlchemyModel = TypeVar("AbstractSQLAlchemyModel", bound=Base)

AbstractSQLAlchemyModelWithPrimaryInt = TypeVar(
    "AbstractSQLAlchemyModelWithPrimaryInt", bound=AbstractModelWithIntID
)

AbstractSQLAlchemyModelWithPrimaryUUID = TypeVar(
    "AbstractSQLAlchemyModelWithPrimaryUUID", bound=AbstractModelWithUUID
)


class AbstractDefaultSQLAlchemyAsyncRepository(
    Generic[
        AbstractSQLAlchemyModel,
        AbstractID,
        AbstractDefaultPydanticModel,
    ],
    ABC,
):
    """Base async repository for SQLAlchemy models.

    Provides session management, user context, and helper methods
    for common database operations like flush and refresh.

    Type Parameters:
        AbstractSQLAlchemyModel: The SQLAlchemy ORM model class.
        AbstractID: The type of the primary key.
        AbstractDefaultPydanticModel: The Pydantic model for output validation.

    Базовый асинхронный репозиторий для SQLAlchemy-моделей.

    Предоставляет управление сессиями, контекст пользователя и вспомогательные
    методы для общих операций с базой данных, таких как flush и refresh.

    Type Parameters:
        AbstractSQLAlchemyModel: Класс SQLAlchemy ORM-модели.
        AbstractID: Тип первичного ключа.
        AbstractDefaultPydanticModel: Pydantic-модель для валидации вывода.
    """

    def __init__(self, session: AsyncSession, user: User):
        """Initialize the repository with a database session and user context.

        Args:
            session: Async SQLAlchemy session.
            user: The authenticated user making the request.

        Инициализирует репозиторий сессией базы данных и контекстом пользователя.

        Args:
            session: Асинхронная сессия SQLAlchemy.
            user: Аутентифицированный пользователь, выполняющий запрос.
        """
        self.__session = session
        self.__user = user

    @property
    def _session(self) -> AsyncSession:
        """Return the async database session.

        Возвращает асинхронную сессию базы данных.
        """
        return self.__session

    @property
    def _user(self) -> User:
        """Return the authenticated user.

        Возвращает аутентифицированного пользователя.
        """
        return self.__user

    @property
    @abstractmethod
    def _model(self) -> AbstractSQLAlchemyModel:
        """Return the SQLAlchemy model class this repository operates on.

        Возвращает класс SQLAlchemy-модели, с которым работает репозиторий.
        """
        pass

    async def _flush_obj(self, obj: AbstractSQLAlchemyModel) -> None:
        """Flush a single object to the database without committing.

        Args:
            obj: The SQLAlchemy model instance to flush.

        Записывает один объект в базу данных без коммита.

        Args:
            obj: Экземпляр SQLAlchemy-модели для записи.
        """
        await self._session.flush(
            objects=[
                obj,
            ]
        )

    async def _flush_many_objs(self, objs: list[AbstractSQLAlchemyModel]) -> None:
        """Flush multiple objects to the database without committing.

        Args:
            objs: List of SQLAlchemy model instances to flush.

        Записывает несколько объектов в базу данных без коммита.

        Args:
            objs: Список экземпляров SQLAlchemy-моделей для записи.
        """
        await self._session.flush(objects=objs)

    async def _refresh_obj(self, obj: AbstractSQLAlchemyModel) -> None:
        """Refresh a single object from the database.

        Args:
            obj: The SQLAlchemy model instance to refresh.

        Обновляет один объект из базы данных.

        Args:
            obj: Экземпляр SQLAlchemy-модели для обновления.
        """
        await self._session.refresh(instance=obj)

    async def _refresh_objs(self, objs: list[AbstractSQLAlchemyModel]) -> None:
        """Refresh multiple objects from the database.

        Args:
            objs: List of SQLAlchemy model instances to refresh.

        Обновляет несколько объектов из базы данных.

        Args:
            objs: Список экземпляров SQLAlchemy-моделей для обновления.
        """
        for obj in objs:
            await self._refresh_obj(obj=obj)

    @abstractmethod
    async def _get_one_obj_using_id(self, id: AbstractID) -> AbstractSQLAlchemyModel:
        """Retrieve a single object by its ID.

        Args:
            id: The primary key value.

        Returns:
            The SQLAlchemy model instance.

        Получает один объект по его ID.

        Args:
            id: Значение первичного ключа.

        Returns:
            Экземпляр SQLAlchemy-модели.
        """
        pass

    @abstractmethod
    async def _based_select(self) -> Select:
        """Build and return a base SELECT statement for this repository.

        Returns:
            A SQLAlchemy Select object with the base query.

        Формирует и возвращает базовый SELECT-запрос для этого репозитория.

        Returns:
            Объект SQLAlchemy Select с базовым запросом.
        """
        pass

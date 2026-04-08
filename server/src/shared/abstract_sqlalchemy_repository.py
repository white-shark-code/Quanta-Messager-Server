from asyncio import gather
from abc import ABC, abstractmethod
from collections.abc import Coroutine
from typing import Any, Generic, TypeVar

from sqlalchemy.sql import Select
from database import Base
from sqlalchemy.ext.asyncio import AsyncSession
from .abstract_repository import AbstractID, AbstractDefaultPydanticModel


AbstractSQLAlchemyModel = TypeVar(
    'AbstractSQLAlchemyModel',
    bound=Base
)


class AbstractDefaultSQLAlchemyAsyncRepository(
    Generic[
        AbstractSQLAlchemyModel,
        AbstractID,
        AbstractDefaultPydanticModel,
    ],
    ABC
):
    def __init__(self, session: AsyncSession):
        self.__session = session

    @property
    def _session(self) -> AsyncSession:
        return self.__session

    @property
    @abstractmethod
    def _model(self) -> AbstractSQLAlchemyModel:
        pass

    async def _flush_obj(self, obj: AbstractSQLAlchemyModel) -> None:
        await self._session.flush(objects=[obj,])

    async def _flush_many_objs(self, objs: list[AbstractSQLAlchemyModel]) -> None:
        await self._session.flush(objects=objs)

    async def _refresh_obj(self, obj: AbstractSQLAlchemyModel) -> None:
        await self._session.refresh(instance=obj)

    async def _refresh_objs(self, objs: list[AbstractSQLAlchemyModel]) -> None:
        for obj in objs:
            await self._refresh_obj(obj=obj)

    @abstractmethod
    async def _get_one_obj_using_id(
        self,
        id: AbstractID
    ) -> AbstractSQLAlchemyModel:
        pass

    @abstractmethod
    async def _based_select(
        self
    ) -> Select:
        pass

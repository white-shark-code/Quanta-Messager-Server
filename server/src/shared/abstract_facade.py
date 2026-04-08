from typing import Generic, TypeVar
from abc import ABC

from .abstract_schemas import (
    AbstractCreateBaseModel,
    AbstractDefaultBaseModel,
    AbstractDefaultPagginationBaseModel,
    AbstractDeleteBaseModel,
    AbstractReadBaseModel,
    AbstractDefaultReadPagginationBaseModel,
    AbstractUpdateBaseModel,
)
from .exceptions import AppException

# TypeVar для репозитория (оставляем свободным, чтобы не тянуть Any во все дженерики)
AbstractRepo = TypeVar('AbstractRepo')

# TypeVar для Pydantic схем
AbstractDefaultPydanticModel = TypeVar('AbstractDefaultPydanticModel', bound=AbstractDefaultBaseModel)
AbstractPostPydanticModel = TypeVar('AbstractPostPydanticModel', bound=AbstractCreateBaseModel)
AbstractGetPydanticModel = TypeVar('AbstractGetPydanticModel', bound=AbstractReadBaseModel)
AbstractPatchPydanticModel = TypeVar('AbstractPatchPydanticModel', bound=AbstractUpdateBaseModel)
AbstractDeletePydanticModel = TypeVar('AbstractDeletePydanticModel', bound=AbstractDeleteBaseModel)
AbstractGetPagginatedPydanticModel = TypeVar('AbstractGetPagginatedPydanticModel', bound=AbstractDefaultReadPagginationBaseModel)
AbstractDefaultPagginatedPydanticModel = TypeVar('AbstractDefaultPagginatedPydanticModel', bound=AbstractDefaultPagginationBaseModel)

# TypeVar для кастомных исключений
AbstractAppException = TypeVar('AbstractAppException', bound=AppException)


class AbstractFacadeCRUDP(
    Generic[
        AbstractRepo,
        AbstractDefaultPydanticModel,
        AbstractPostPydanticModel,
        AbstractGetPydanticModel,
        AbstractPatchPydanticModel,
        AbstractDeletePydanticModel,
        AbstractGetPagginatedPydanticModel,
        AbstractDefaultPagginatedPydanticModel,
        AbstractAppException
    ],
    ABC
):
    def __init__(self, repo: AbstractRepo):
        self._repo = repo

    # --- Create ---
    async def _before_create(self, schema: AbstractPostPydanticModel) -> AbstractPostPydanticModel:
        return schema

    async def _after_create(self, result: AbstractDefaultPydanticModel) -> None:
        pass

    async def create(self, schema: AbstractPostPydanticModel) -> AbstractDefaultPydanticModel:
        schema = await self._before_create(schema)
        result = await self._repo.post(post_schema=schema)
        await self._after_create(result)
        return result

    # --- Read ---
    async def _before_read(self, schema: AbstractGetPydanticModel) -> AbstractGetPydanticModel:
        return schema

    async def _after_read(self, result: AbstractDefaultPydanticModel) -> None:
        pass

    async def read(self, schema: AbstractGetPydanticModel) -> AbstractDefaultPydanticModel:
        schema = await self._before_read(schema)
        result = await self._repo.get(get_schema=schema)
        await self._after_read(result)
        return result

    # --- Update ---
    async def _before_update(self, schema: AbstractPatchPydanticModel) -> AbstractPatchPydanticModel:
        return schema

    async def _after_update(self, result: AbstractDefaultPydanticModel) -> None:
        pass

    async def update(self, schema: AbstractPatchPydanticModel) -> AbstractDefaultPydanticModel:
        schema = await self._before_update(schema)
        result = await self._repo.patch(patch_schema=schema)
        await self._after_update(result)
        return result

    # --- Delete ---
    async def _before_delete(self, schema: AbstractDeletePydanticModel) -> AbstractDeletePydanticModel:
        return schema

    async def _after_delete(self, result: AbstractDefaultPydanticModel) -> None:
        pass

    async def delete(self, schema: AbstractDeletePydanticModel) -> AbstractDefaultPydanticModel:
        schema = await self._before_delete(schema)
        result = await self._repo.delete(delete_schema=schema)
        await self._after_delete(result)
        return result

    # --- Read Paginated ---
    async def _before_read_paginated(self, schema: AbstractGetPagginatedPydanticModel) -> AbstractGetPagginatedPydanticModel:
        return schema

    async def _after_read_paginated(self, result: AbstractDefaultPagginatedPydanticModel) -> None:
        pass

    async def read_paginated(self, schema: AbstractGetPagginatedPydanticModel) -> AbstractDefaultPagginatedPydanticModel:
        schema = await self._before_read_paginated(schema)
        result = await self._repo.get_many(get_schema=schema)
        await self._after_read_paginated(result)
        return result

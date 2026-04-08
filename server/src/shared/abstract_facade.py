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

AbstractRepo = TypeVar('AbstractRepo')

AbstractDefaultPydanticModel = TypeVar('AbstractDefaultPydanticModel', bound=AbstractDefaultBaseModel)
AbstractPostPydanticModel = TypeVar('AbstractPostPydanticModel', bound=AbstractCreateBaseModel)
AbstractGetPydanticModel = TypeVar('AbstractGetPydanticModel', bound=AbstractReadBaseModel)
AbstractPatchPydanticModel = TypeVar('AbstractPatchPydanticModel', bound=AbstractUpdateBaseModel)
AbstractDeletePydanticModel = TypeVar('AbstractDeletePydanticModel', bound=AbstractDeleteBaseModel)
AbstractGetPagginatedPydanticModel = TypeVar('AbstractGetPagginatedPydanticModel', bound=AbstractDefaultReadPagginationBaseModel)
AbstractDefaultPagginatedPydanticModel = TypeVar('AbstractDefaultPagginatedPydanticModel', bound=AbstractDefaultPagginationBaseModel)


class AbstractFacadeBase(Generic[AbstractRepo], ABC):
    def __init__(self, repo: AbstractRepo):
        self._repo = repo


class AbstractFacadeCreate(
    Generic[AbstractRepo, AbstractDefaultPydanticModel, AbstractPostPydanticModel],
    AbstractFacadeBase[AbstractRepo],
    ABC
):
    async def _before_create(self, schema: AbstractPostPydanticModel) -> AbstractPostPydanticModel:
        return schema

    async def _after_create(self, result: AbstractDefaultPydanticModel) -> None:
        pass

    async def create(self, schema: AbstractPostPydanticModel) -> AbstractDefaultPydanticModel:
        schema = await self._before_create(schema)
        result = await self._repo.post(post_schema=schema)
        await self._after_create(result)
        return result


class AbstractFacadeRead(
    Generic[AbstractRepo, AbstractDefaultPydanticModel, AbstractGetPydanticModel],
    AbstractFacadeBase[AbstractRepo],
    ABC
):
    async def _before_read(self, schema: AbstractGetPydanticModel) -> AbstractGetPydanticModel:
        return schema

    async def _after_read(self, result: AbstractDefaultPydanticModel) -> None:
        pass

    async def read(self, schema: AbstractGetPydanticModel) -> AbstractDefaultPydanticModel:
        schema = await self._before_read(schema)
        result = await self._repo.get(get_schema=schema)
        await self._after_read(result)
        return result


class AbstractFacadeUpdate(
    Generic[AbstractRepo, AbstractDefaultPydanticModel, AbstractPatchPydanticModel],
    AbstractFacadeBase[AbstractRepo],
    ABC
):
    async def _before_update(self, schema: AbstractPatchPydanticModel) -> AbstractPatchPydanticModel:
        return schema

    async def _after_update(self, result: AbstractDefaultPydanticModel) -> None:
        pass

    async def update(self, schema: AbstractPatchPydanticModel) -> AbstractDefaultPydanticModel:
        schema = await self._before_update(schema)
        result = await self._repo.patch(patch_schema=schema)
        await self._after_update(result)
        return result


class AbstractFacadeDelete(
    Generic[AbstractRepo, AbstractDefaultPydanticModel, AbstractDeletePydanticModel],
    AbstractFacadeBase[AbstractRepo],
    ABC
):
    async def _before_delete(self, schema: AbstractDeletePydanticModel) -> AbstractDeletePydanticModel:
        return schema

    async def _after_delete(self, result: AbstractDefaultPydanticModel) -> None:
        pass

    async def delete(self, schema: AbstractDeletePydanticModel) -> AbstractDefaultPydanticModel:
        schema = await self._before_delete(schema)
        result = await self._repo.delete(delete_schema=schema)
        await self._after_delete(result)
        return result


class AbstractFacadeReadPaginated(
    Generic[AbstractRepo, AbstractDefaultPagginatedPydanticModel, AbstractGetPagginatedPydanticModel],
    AbstractFacadeBase[AbstractRepo],
    ABC
):
    async def _before_read_paginated(self, schema: AbstractGetPagginatedPydanticModel) -> AbstractGetPagginatedPydanticModel:
        return schema

    async def _after_read_paginated(self, result: AbstractDefaultPagginatedPydanticModel) -> None:
        pass

    async def read_paginated(self, schema: AbstractGetPagginatedPydanticModel) -> AbstractDefaultPagginatedPydanticModel:
        schema = await self._before_read_paginated(schema)
        result = await self._repo.get_many(get_schema=schema)
        await self._after_read_paginated(result)
        return result


# --- Комбинации Фасадов ---

class AbstractFacadeCR(
    Generic[AbstractRepo, AbstractDefaultPydanticModel, AbstractPostPydanticModel, AbstractGetPydanticModel],
    AbstractFacadeCreate[AbstractRepo, AbstractDefaultPydanticModel, AbstractPostPydanticModel],
    AbstractFacadeRead[AbstractRepo, AbstractDefaultPydanticModel, AbstractGetPydanticModel],
    ABC
):
    pass


class AbstractFacadeCRU(
    Generic[AbstractRepo, AbstractDefaultPydanticModel, AbstractPostPydanticModel, AbstractGetPydanticModel, AbstractPatchPydanticModel],
    AbstractFacadeCreate[AbstractRepo, AbstractDefaultPydanticModel, AbstractPostPydanticModel],
    AbstractFacadeRead[AbstractRepo, AbstractDefaultPydanticModel, AbstractGetPydanticModel],
    AbstractFacadeUpdate[AbstractRepo, AbstractDefaultPydanticModel, AbstractPatchPydanticModel],
    ABC
):
    pass


class AbstractFacadeCRD(
    Generic[AbstractRepo, AbstractDefaultPydanticModel, AbstractPostPydanticModel, AbstractGetPydanticModel, AbstractDeletePydanticModel],
    AbstractFacadeCreate[AbstractRepo, AbstractDefaultPydanticModel, AbstractPostPydanticModel],
    AbstractFacadeRead[AbstractRepo, AbstractDefaultPydanticModel, AbstractGetPydanticModel],
    AbstractFacadeDelete[AbstractRepo, AbstractDefaultPydanticModel, AbstractDeletePydanticModel],
    ABC
):
    pass


class AbstractFacadeRUD(
    Generic[AbstractRepo, AbstractDefaultPydanticModel, AbstractGetPydanticModel, AbstractPatchPydanticModel, AbstractDeletePydanticModel],
    AbstractFacadeRead[AbstractRepo, AbstractDefaultPydanticModel, AbstractGetPydanticModel],
    AbstractFacadeUpdate[AbstractRepo, AbstractDefaultPydanticModel, AbstractPatchPydanticModel],
    AbstractFacadeDelete[AbstractRepo, AbstractDefaultPydanticModel, AbstractDeletePydanticModel],
    ABC
):
    pass


class AbstractFacadeCRUD(
    Generic[AbstractRepo, AbstractDefaultPydanticModel, AbstractPostPydanticModel, AbstractGetPydanticModel, AbstractPatchPydanticModel, AbstractDeletePydanticModel],
    AbstractFacadeCreate[AbstractRepo, AbstractDefaultPydanticModel, AbstractPostPydanticModel],
    AbstractFacadeRead[AbstractRepo, AbstractDefaultPydanticModel, AbstractGetPydanticModel],
    AbstractFacadeUpdate[AbstractRepo, AbstractDefaultPydanticModel, AbstractPatchPydanticModel],
    AbstractFacadeDelete[AbstractRepo, AbstractDefaultPydanticModel, AbstractDeletePydanticModel],
    ABC
):
    pass


class AbstractFacadeCRUP(
    Generic[AbstractRepo, AbstractDefaultPydanticModel, AbstractPostPydanticModel, AbstractGetPydanticModel, AbstractPatchPydanticModel, AbstractGetPagginatedPydanticModel, AbstractDefaultPagginatedPydanticModel],
    AbstractFacadeCreate[AbstractRepo, AbstractDefaultPydanticModel, AbstractPostPydanticModel],
    AbstractFacadeRead[AbstractRepo, AbstractDefaultPydanticModel, AbstractGetPydanticModel],
    AbstractFacadeUpdate[AbstractRepo, AbstractDefaultPydanticModel, AbstractPatchPydanticModel],
    AbstractFacadeReadPaginated[AbstractRepo, AbstractDefaultPagginatedPydanticModel, AbstractGetPagginatedPydanticModel],
    ABC
):
    pass


class AbstractFacadeCRDP(
    Generic[AbstractRepo, AbstractDefaultPydanticModel, AbstractPostPydanticModel, AbstractGetPydanticModel, AbstractDeletePydanticModel, AbstractGetPagginatedPydanticModel, AbstractDefaultPagginatedPydanticModel],
    AbstractFacadeCreate[AbstractRepo, AbstractDefaultPydanticModel, AbstractPostPydanticModel],
    AbstractFacadeRead[AbstractRepo, AbstractDefaultPydanticModel, AbstractGetPydanticModel],
    AbstractFacadeDelete[AbstractRepo, AbstractDefaultPydanticModel, AbstractDeletePydanticModel],
    AbstractFacadeReadPaginated[AbstractRepo, AbstractDefaultPagginatedPydanticModel, AbstractGetPagginatedPydanticModel],
    ABC
):
    pass


class AbstractFacadeRUDP(
    Generic[AbstractRepo, AbstractDefaultPydanticModel, AbstractGetPydanticModel, AbstractPatchPydanticModel, AbstractDeletePydanticModel, AbstractGetPagginatedPydanticModel, AbstractDefaultPagginatedPydanticModel],
    AbstractFacadeRead[AbstractRepo, AbstractDefaultPydanticModel, AbstractGetPydanticModel],
    AbstractFacadeUpdate[AbstractRepo, AbstractDefaultPydanticModel, AbstractPatchPydanticModel],
    AbstractFacadeDelete[AbstractRepo, AbstractDefaultPydanticModel, AbstractDeletePydanticModel],
    AbstractFacadeReadPaginated[AbstractRepo, AbstractDefaultPagginatedPydanticModel, AbstractGetPagginatedPydanticModel],
    ABC
):
    pass


class AbstractFacadeCRUDP(
    Generic[AbstractRepo, AbstractDefaultPydanticModel, AbstractPostPydanticModel, AbstractGetPydanticModel, AbstractPatchPydanticModel, AbstractDeletePydanticModel, AbstractGetPagginatedPydanticModel, AbstractDefaultPagginatedPydanticModel],
    AbstractFacadeCreate[AbstractRepo, AbstractDefaultPydanticModel, AbstractPostPydanticModel],
    AbstractFacadeRead[AbstractRepo, AbstractDefaultPydanticModel, AbstractGetPydanticModel],
    AbstractFacadeUpdate[AbstractRepo, AbstractDefaultPydanticModel, AbstractPatchPydanticModel],
    AbstractFacadeDelete[AbstractRepo, AbstractDefaultPydanticModel, AbstractDeletePydanticModel],
    AbstractFacadeReadPaginated[AbstractRepo, AbstractDefaultPagginatedPydanticModel, AbstractGetPagginatedPydanticModel],
    ABC
):
    pass

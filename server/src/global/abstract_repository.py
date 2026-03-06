from typing import Generic, TypeVar
from .abstract_schemas import (
    AbstractCreateBaseModel,
    AbstractDefaultBaseModel,
    AbstractDefaultPagginationBaseModel,
    AbstractDeleteBaseModel,
    AbstractReadBaseModel,
    AbstractReadPagginationBaseModel,
    AbstractUpdateBaseModel,
)
from abc import (
    abstractmethod,
    ABC,
)


AbstractDefaultPydanticModel = TypeVar(
    'AbstractDefaultPydanticModel',
    bound=AbstractDefaultBaseModel
)
AbstractPostPydanticModel = TypeVar(
    'AbstractPostPydanticModel',
    bound=AbstractCreateBaseModel
)
AbstractGetPydanticModel = TypeVar(
    'AbstractGetPydanticModel',
    bound=AbstractReadBaseModel
)
AbstractDeletePydanticModel = TypeVar(
    'AbstractDeletePydanticModel',
    bound=AbstractDeleteBaseModel
)


class AbstractAsyncPGDEntity(
    Generic[
        AbstractDefaultPydanticModel,
        AbstractPostPydanticModel,
        AbstractGetPydanticModel,
        AbstractDeletePydanticModel
    ],
    ABC,
):

    async def _before_post(self):
        pass

    @abstractmethod
    async def _post(
        self,
        post_schema: AbstractPostPydanticModel
    ) -> AbstractDefaultPydanticModel:
        pass

    async def post(
        self,
        post_schema: AbstractPostPydanticModel
    ) -> AbstractDefaultPydanticModel:
        await self._before_post()
        return await self._post(post_schema=post_schema)

    async def _before_get(self):
        pass

    @abstractmethod
    async def _get(
        self,
        get_schema: AbstractGetPydanticModel
    ) -> AbstractDefaultPydanticModel:
        pass

    async def get(
        self,
        get_schema: AbstractGetPydanticModel
    ) -> AbstractDefaultPydanticModel:
        await self._before_get()
        return await self._get(get_schema=get_schema)

    async def _before_delete(self):
        pass

    @abstractmethod
    async def _delete(
        self,
        delete_schema: AbstractDeletePydanticModel
    ) -> AbstractDefaultPydanticModel:
        pass

    async def delete(
        self,
        delete_schema: AbstractDeletePydanticModel
    ) -> AbstractDefaultPydanticModel:
        await self._before_delete()
        return await self._delete(delete_schema=delete_schema)


AbstractPatchPydanticModel = TypeVar(
    'AbstractPatchPydanticModel',
    bound=AbstractUpdateBaseModel
)


class AbstractAsyncPGPDEntity(
    AbstractAsyncPGDEntity,
    Generic[
        AbstractDefaultPydanticModel,
        AbstractPostPydanticModel,
        AbstractGetPydanticModel,
        AbstractDeletePydanticModel,
        AbstractPatchPydanticModel
    ],
    ABC
):
    async def _before_patch(self):
        pass

    @abstractmethod
    async def _patch(
        self,
        patch_schema: AbstractPatchPydanticModel
    ) -> AbstractDefaultPydanticModel:
        pass

    async def patch(
        self,
        patch_schema: AbstractPatchPydanticModel
    ) -> AbstractDefaultPydanticModel:
        await self._before_patch()
        return await self._patch(patch_schema=patch_schema)



AbstractGetPagginatedPydanticModel = TypeVar(
    'AbstractGetPagginatedPydanticModel',
    bound=AbstractReadPagginationBaseModel
)
AbstractDefaultPydanticModel = TypeVar(
    'AbstractDefaultPydanticModel',
    bound=AbstractDefaultPagginationBaseModel
)


class AbstractAsyncPGDEntityPagginated(
    Generic[
        AbstractGetPagginatedPydanticModel,
        AbstractDefaultPydanticModel
    ],
    ABC
):
    async def _before_get_many(self):
        pass

    @abstractmethod
    async def _get_many(
        self,
        get_schema: AbstractGetPagginatedPydanticModel
    ) -> AbstractDefaultPydanticModel:
        pass

    async def get_many(
        self,
        get_schema: AbstractGetPagginatedPydanticModel
    ) -> AbstractDefaultPydanticModel:
        await self._before_get_many()
        return await self._get_many(get_schema=get_schema)

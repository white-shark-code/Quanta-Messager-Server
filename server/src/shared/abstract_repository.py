from typing import (
    Generic,
    TypeVar,
    Any,
)
from .abstract_schemas import (
    AbstractID,
    AbstractItem,
    AbstractCreateBaseModel,
    AbstractDefaultBaseModel,
    AbstractDefaultPagginationBaseModel,
    AbstractDeleteBaseModel,
    AbstractReadBaseModel,
    AbstractDefaultReadPagginationBaseModel,
    AbstractUpdateBaseModel,
)
from abc import abstractmethod, ABC


AbstractDefaultPydanticModel = TypeVar(
    'AbstractDefaultPydanticModel',
    bound=AbstractDefaultBaseModel
)
AbstractPostPydanticModel = TypeVar(
    'AbstractPostPydanticModel',
    bound=AbstractCreateBaseModel
)


class GenericAsyncRepo(
    Generic[AbstractDefaultPydanticModel],
    ABC
):
    @property
    @abstractmethod
    def _output_pyd_model(self) -> type[AbstractDefaultPydanticModel]:
        pass


class AbstractAsyncRepoCreate(
    Generic[
        AbstractPostPydanticModel,
        AbstractDefaultPydanticModel
    ],
    GenericAsyncRepo[AbstractDefaultPydanticModel],    
    ABC,
):

    async def _before_post(self):
        pass

    @abstractmethod
    async def _post(
        self,
        post_schema: AbstractPostPydanticModel
    ) -> Any:
        pass

    async def post(
        self,
        post_schema: AbstractPostPydanticModel
    ) -> AbstractDefaultPydanticModel:
        await self._before_post()
        return self._output_pyd_model.model_validate(
            await self._post(post_schema=post_schema)
        )


AbstractGetPydanticModel = TypeVar(
    'AbstractGetPydanticModel',
    bound=AbstractReadBaseModel
)


class AbstractAsyncRepoRead(
    Generic[
        AbstractDefaultPydanticModel,
        AbstractGetPydanticModel
    ],
    GenericAsyncRepo[AbstractDefaultPydanticModel],
    ABC,
):

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
        return self._output_pyd_model.model_validate(
            await self._get(get_schema=get_schema)
        )


AbstractPatchPydanticModel = TypeVar(
    'AbstractUpdatePydanticModel',
    bound=AbstractUpdateBaseModel
)


class AbstractAsyncRepoUpdate(
    Generic[
        AbstractDefaultPydanticModel,
        AbstractPatchPydanticModel
    ],
    GenericAsyncRepo[AbstractDefaultPydanticModel],
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
        return self._output_pyd_model.model_validate(
            await self._patch(patch_schema=patch_schema)
        )


AbstractDeletePydanticModel = TypeVar(
    'AbstractDeletePydanticModel',
    bound=AbstractDeleteBaseModel
)


class AbstractAsyncRepoDelete(
    Generic[
        AbstractDefaultPydanticModel,
        AbstractDeletePydanticModel
    ],
    GenericAsyncRepo[AbstractDefaultPydanticModel],
    ABC,
):

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
        return self._output_pyd_model.model_validate(
            await self._delete(delete_schema=delete_schema)
        )


AbstractGetPagginatedPydanticModel = TypeVar(
    'AbstractGetPagginatedPydanticModel',
    bound=AbstractDefaultReadPagginationBaseModel
)
AbstractDefaultPagginatedPydanticModel = TypeVar(
    'AbstractDefaultPagginatedPydanticModel',
    bound=AbstractDefaultPagginationBaseModel
)


class AbstractAsyncRepoReadPagginated(
    Generic[
        AbstractID,
        AbstractGetPagginatedPydanticModel,
        AbstractDefaultPagginatedPydanticModel
    ],
    ABC
):
    @property
    @abstractmethod
    def _pagginated_output_pyd_model(self) -> \
        type[AbstractDefaultPagginatedPydanticModel]:
        pass

    async def _before_get_many(self):
        pass

    @abstractmethod
    async def _get_many(
        self,
        get_schema: AbstractGetPagginatedPydanticModel
    ) -> list[Any]:
        pass

    @abstractmethod
    async def _get_count(
        self,
        get_schema: AbstractGetPagginatedPydanticModel
    ) -> int:
        pass

    async def _get_prepaired_dict(
        self,
        get_schema: AbstractGetPagginatedPydanticModel
    ) -> dict[str, int | list[AbstractItem] | AbstractID ]:
        count = await self._get_count(get_schema)
        items = await self._get_many(get_schema)
        return {
            'count_pages': int(count / get_schema.page_size + 0.5),
            'items': items,
            'page_size': get_schema.page_size
        }


    async def get_many(
        self,
        get_schema: AbstractGetPagginatedPydanticModel
    ) -> AbstractDefaultPagginatedPydanticModel:
        await self._before_get_many()
        data = await self._get_prepaired_dict(get_schema)
        return self._pagginated_output_pyd_model.model_validate(
            **data
        )


class AbstractAsyncCRUDPRepo(
    Generic[
        AbstractID,
        AbstractDefaultPydanticModel,
        AbstractPostPydanticModel,
        AbstractGetPydanticModel,
        AbstractPatchPydanticModel,
        AbstractDeletePydanticModel,
        AbstractGetPagginatedPydanticModel,
        AbstractDefaultPagginatedPydanticModel
    ],
    AbstractAsyncRepoCreate[AbstractPostPydanticModel, AbstractDefaultPydanticModel],
    AbstractAsyncRepoRead[AbstractDefaultPydanticModel, AbstractGetPydanticModel],
    AbstractAsyncRepoUpdate[AbstractDefaultPydanticModel, AbstractPatchPydanticModel],
    AbstractAsyncRepoDelete[AbstractDefaultPydanticModel, AbstractDeletePydanticModel],
    AbstractAsyncRepoReadPagginated[AbstractID, AbstractGetPagginatedPydanticModel, AbstractDefaultPagginatedPydanticModel],
    ABC
):
    pass

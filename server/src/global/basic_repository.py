from typing import TypeVar, Generic
from abc import abstractmethod
from uuid import UUID
from sqlalchemy import (
    Result,
    ChunkedIteratorResult,
    Select,
    select,
    func
)
from .abstract_repository import (
    AbstractDefaultPydanticModel,
    AbstractPostPydanticModel,
    AbstractGetPydanticModel,
    AbstractDeletePydanticModel,
    AbstractPatchPydanticModel,
    AbstractGetPagginatedPydanticModel,
    AbstractDefaultPagginatedPydanticModel,
    AbstractAsyncRepoCreate,
    AbstractAsyncRepoRead,
    AbstractAsyncRepoUpdate,
    AbstractAsyncRepoDelete,
    AbstractDeleteBaseModel,
    AbstractAsyncRepoReadPagginated,
)
from .abstract_schemas import (
    AbstractDefaultBaseModel,
    AbstractID,
    AbstractIntPagginationBaseModel,
    AbstractUUIDPagginationBaseModel
)
from .abstract_sqlalchemy_repository import (
    AbstractDefaultSQLAlchemyAsyncRepository,
    AbstractSQLAlchemyModel
)
from .basic_schemas import (
    IntReadPagginationBaseModel,
    UUIDReadPagginationBaseModel
)


class AbstractDefaultSQLAlchemyCreate(
    AbstractDefaultSQLAlchemyAsyncRepository,
    AbstractAsyncRepoCreate[
        AbstractSQLAlchemyModel,
        AbstractID,
        AbstractDefaultPydanticModel,
        AbstractPostPydanticModel,
    ]
):
    async def _post(
        self,
        post_schema: AbstractPostPydanticModel
    ) -> AbstractSQLAlchemyModel:
        new = self._model(
            **post_schema.model_dump()
        )
        self._session.add(new)
        self._session.refresh(new)
        return new


class AbstractDefaultSQLAlchemyRead(
    AbstractDefaultSQLAlchemyAsyncRepository,
    AbstractAsyncRepoRead[
        AbstractSQLAlchemyModel,
        AbstractID,
        AbstractDefaultPydanticModel,
        AbstractGetPydanticModel,
    ]
):

    async def _get(
        self,
        get_schema: AbstractGetPydanticModel
    ) -> AbstractSQLAlchemyModel | None:
        return await self._session.get(self._model, get_schema.id)


class AbstractDefaultSQLAlchemyUpdate(
    AbstractDefaultSQLAlchemyAsyncRepository,
    AbstractAsyncRepoUpdate[
        AbstractSQLAlchemyModel,
        AbstractID,
        AbstractDefaultPydanticModel,
        AbstractPatchPydanticModel
    ]
):
    async def _patch(
        self,
        update_schema: AbstractPatchPydanticModel
    ) -> AbstractSQLAlchemyModel:
        obj = await self._session.get(
            self._model,
            update_schema.id
        )
        update_data = update_schema.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(obj, key, value)
        self._session.refresh(obj)
        return obj


class AbstractDefaultSQLAlchemyDelete(
    AbstractDefaultSQLAlchemyAsyncRepository,
    AbstractAsyncRepoDelete[
        AbstractSQLAlchemyModel,
        AbstractID,
        AbstractDefaultPydanticModel,
        AbstractDeletePydanticModel
    ]
):
    async def _delete(
        self,
        delete_schema: AbstractDeletePydanticModel
    ) -> AbstractSQLAlchemyModel:
        obj = await self._session.get(
            self._model,
            delete_schema.id
        )
        self._session.delete(obj)
        return obj


class AbstractDefaultSQLAlchemyReadPagginated(
    AbstractDefaultSQLAlchemyAsyncRepository,
    AbstractAsyncRepoReadPagginated[
        AbstractID,
        AbstractGetPagginatedPydanticModel,
        AbstractDefaultPagginatedPydanticModel
    ],
    Generic[
        AbstractSQLAlchemyModel
    ]
):
    @abstractmethod
    def _get_many_stmt(
        self,
        get_schema: AbstractGetPagginatedPydanticModel
    ) -> Select:
        pass

    async def _get_many(
        self,
        get_schema: AbstractGetPagginatedPydanticModel
    ) -> list[AbstractSQLAlchemyModel]:
        stmt = self._get_many_stmt(get_schema)
        result = await self._session.execute(stmt)
        return result.scalars().all()

    async def _get_count(
        self,
        get_schema: AbstractGetPagginatedPydanticModel
    ) -> int:
        stmt = self._get_many_stmt(get_schema)
        count_stmt = select(func.count()).select_from(stmt.subquery())
        count_result = await self._session.execute(count_stmt)
        return count_result.scalar_one()

    async def get_many(
        self,
        get_schema: AbstractGetPagginatedPydanticModel
    ) -> AbstractDefaultPagginatedPydanticModel:
        await self._before_get_many()
        data = await self._get_prepaired_dict(get_schema)
        return self._pagginated_output_pyd_model.model_validate(**data) 


AbstractIntPaggination = TypeVar(
    'AbstractIntPaggination',
    bound=AbstractIntPagginationBaseModel
)


class AbstractIntSQLAlchemyReadPagginated(
    AbstractDefaultSQLAlchemyReadPagginated[
        int,
        IntReadPagginationBaseModel,
        AbstractIntPaggination,
        AbstractSQLAlchemyModel
    ]
):
    async def _get_prepaired_dict(
        self,
        get_schema: AbstractGetPagginatedPydanticModel
    ) -> dict[str, int | list[AbstractSQLAlchemyModel]]:
        prepaired_dict = super()._get_prepaired_dict(get_schema)
        prepaired_dict['last_id'] = prepaired_dict['items'][-1].id
        return prepaired_dict


AbstractUUIDPaggination = TypeVar(
    'AbstractUUIDPaggination',
    bound=AbstractUUIDPagginationBaseModel
)


class AbstractUUIDSQLAlchemyReadPagginated(
    AbstractDefaultSQLAlchemyReadPagginated[
        UUID,
        UUIDReadPagginationBaseModel,
        AbstractUUIDPaggination,
        AbstractSQLAlchemyModel
    ]
):
    async def _get_prepaired_dict(
        self,
        get_schema: AbstractGetPagginatedPydanticModel
    ) -> dict[str, int | list[AbstractSQLAlchemyModel | UUID]]:
        prepaired_dict = super()._get_prepaired_dict(get_schema)
        prepaired_dict['last_id'] = prepaired_dict['items'][-1]['id']
        return prepaired_dict


class AbstractDefaultSQLAlchemyCRUDP(
    AbstractDefaultSQLAlchemyCreate,
    AbstractDefaultSQLAlchemyRead,
    AbstractDefaultSQLAlchemyUpdate,
    AbstractDefaultSQLAlchemyDelete,
    AbstractDefaultSQLAlchemyReadPagginated[
        AbstractSQLAlchemyModel,
        AbstractID,
        AbstractDefaultPydanticModel,
        AbstractPostPydanticModel,
        AbstractGetPydanticModel,
        AbstractPatchPydanticModel,
        AbstractDeletePydanticModel,
        AbstractGetPagginatedPydanticModel,
        AbstractDefaultPagginatedPydanticModel
    ]
):
    pass


class AbstractIntSQLAlchemyCRUDP(
    AbstractDefaultSQLAlchemyCRUDP,
    AbstractIntSQLAlchemyReadPagginated[
        AbstractSQLAlchemyModel,
        int,
        AbstractDefaultPydanticModel,
        AbstractPostPydanticModel,
        AbstractGetPydanticModel,
        AbstractPatchPydanticModel,
        AbstractDeletePydanticModel,
        IntReadPagginationBaseModel,
        AbstractIntPaggination
    ]
):
    pass


class AbstractUUIDSQLAlchemyCRUDP(
    AbstractDefaultSQLAlchemyCRUDP,
    AbstractUUIDSQLAlchemyReadPagginated[
        AbstractSQLAlchemyModel,
        UUID,
        AbstractDefaultPydanticModel,
        AbstractPostPydanticModel,
        AbstractGetPydanticModel,
        AbstractPatchPydanticModel,
        AbstractDeletePydanticModel,
        UUIDReadPagginationBaseModel,
        AbstractUUIDPaggination
    ]
):
    pass

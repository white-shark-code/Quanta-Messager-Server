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
    Generic[
        AbstractSQLAlchemyModel,
        AbstractID,
        AbstractDefaultPydanticModel,
        AbstractPostPydanticModel,
    ],
    AbstractDefaultSQLAlchemyAsyncRepository[
        AbstractSQLAlchemyModel,
        AbstractID,
        AbstractDefaultPydanticModel,
    ],
    AbstractAsyncRepoCreate[
        AbstractPostPydanticModel,
        AbstractDefaultPydanticModel
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
    Generic[
        AbstractSQLAlchemyModel,
        AbstractID,
        AbstractDefaultPydanticModel,
        AbstractGetPydanticModel,
    ],
    AbstractDefaultSQLAlchemyAsyncRepository[
        AbstractSQLAlchemyModel,
        AbstractID,
        AbstractDefaultPydanticModel,
    ],
    AbstractAsyncRepoRead[
        AbstractDefaultPydanticModel,
        AbstractGetPydanticModel
    ]
):

    async def _get(
        self,
        get_schema: AbstractGetPydanticModel
    ) -> AbstractSQLAlchemyModel | None:
        return await self._session.get(self._model, get_schema.id)


class AbstractDefaultSQLAlchemyUpdate(
    Generic[
        AbstractSQLAlchemyModel,
        AbstractID,
        AbstractDefaultPydanticModel,
        AbstractPatchPydanticModel
    ],
    AbstractDefaultSQLAlchemyAsyncRepository[
        AbstractSQLAlchemyModel,
        AbstractID,
        AbstractDefaultPydanticModel,
    ],
    AbstractAsyncRepoUpdate[
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
    Generic[
        AbstractSQLAlchemyModel,
        AbstractID,
        AbstractDefaultPydanticModel,
        AbstractDeletePydanticModel
    ],
    AbstractDefaultSQLAlchemyAsyncRepository[
        AbstractSQLAlchemyModel,
        AbstractID,
        AbstractDefaultPydanticModel,
    ],
    AbstractAsyncRepoDelete[
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
    Generic[
        AbstractSQLAlchemyModel,
        AbstractID,
        AbstractDefaultPydanticModel,
        AbstractGetPagginatedPydanticModel,
        AbstractDefaultPagginatedPydanticModel
    ],
    AbstractDefaultSQLAlchemyAsyncRepository[
        AbstractSQLAlchemyModel,
        AbstractID,
        AbstractDefaultPydanticModel,
    ],
    AbstractAsyncRepoReadPagginated[
        AbstractID,
        AbstractGetPagginatedPydanticModel,
        AbstractDefaultPagginatedPydanticModel
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
    ) -> list[AbstractDefaultPydanticModel]:
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
        return self._pagginated_output_pyd_model.model_validate(data) 


AbstractIntPaggination = TypeVar(
    'AbstractIntPaggination',
    bound=AbstractIntPagginationBaseModel
)


class AbstractIntSQLAlchemyReadPagginated(
    Generic[
        AbstractSQLAlchemyModel,
        AbstractIntPaggination,
        AbstractDefaultPydanticModel
    ],
    AbstractDefaultSQLAlchemyReadPagginated[
        AbstractSQLAlchemyModel,
        int,
        IntReadPagginationBaseModel,
        AbstractIntPaggination,
        AbstractDefaultPydanticModel
    ]
):
    async def _get_prepaired_dict(
        self,
        get_schema: AbstractGetPagginatedPydanticModel
    ) -> dict[str, int | list[AbstractDefaultPydanticModel]]:
        prepaired_dict = super()._get_prepaired_dict(get_schema)
        prepaired_dict['last_id'] = prepaired_dict['items'][-1].id
        return prepaired_dict


AbstractUUIDPaggination = TypeVar(
    'AbstractUUIDPaggination',
    bound=AbstractUUIDPagginationBaseModel
)


class AbstractUUIDSQLAlchemyReadPagginated(
    Generic[
        AbstractSQLAlchemyModel,
        AbstractUUIDPaggination,
        AbstractDefaultPydanticModel
    ],
    AbstractDefaultSQLAlchemyReadPagginated[
        AbstractSQLAlchemyModel,
        UUID,
        UUIDReadPagginationBaseModel,
        AbstractUUIDPaggination,
        AbstractDefaultPydanticModel
    ]
):
    async def _get_prepaired_dict(
        self,
        get_schema: AbstractGetPagginatedPydanticModel
    ) -> dict[str, int | list[AbstractDefaultPydanticModel | UUID]]:
        prepaired_dict = super()._get_prepaired_dict(get_schema)
        prepaired_dict['last_id'] = prepaired_dict['items'][-1].id
        return prepaired_dict


class AbstractDefaultSQLAlchemyCRDP(
    Generic[
        AbstractSQLAlchemyModel,
        AbstractID,
        AbstractDefaultPydanticModel,
        AbstractPostPydanticModel,
        AbstractGetPydanticModel,
        AbstractDeletePydanticModel,
        AbstractGetPagginatedPydanticModel,
        AbstractDefaultPagginatedPydanticModel
    ],
    AbstractDefaultSQLAlchemyCreate[
        AbstractSQLAlchemyModel,
        AbstractID,
        AbstractDefaultPydanticModel,
        AbstractPostPydanticModel,
    ],
    AbstractDefaultSQLAlchemyRead[
        AbstractSQLAlchemyModel,
        AbstractID,
        AbstractDefaultPydanticModel,
        AbstractGetPydanticModel,
    ],
    AbstractDefaultSQLAlchemyDelete[
        AbstractSQLAlchemyModel,
        AbstractID,
        AbstractDefaultPydanticModel,
        AbstractDeletePydanticModel
    ],
    AbstractDefaultSQLAlchemyReadPagginated[
        AbstractSQLAlchemyModel,
        AbstractID,
        AbstractDefaultPydanticModel,
        AbstractGetPagginatedPydanticModel,
        AbstractDefaultPagginatedPydanticModel
    ]
):
    pass


class AbstractDefaultSQLAlchemyCRUDP(
    Generic[
        AbstractSQLAlchemyModel,
        AbstractID,
        AbstractDefaultPydanticModel,
        AbstractPostPydanticModel,
        AbstractGetPydanticModel,
        AbstractPatchPydanticModel,
        AbstractDeletePydanticModel,
        AbstractGetPagginatedPydanticModel,
        AbstractDefaultPagginatedPydanticModel
    ],
    AbstractDefaultSQLAlchemyCreate[
        AbstractSQLAlchemyModel,
        AbstractID,
        AbstractDefaultPydanticModel,
        AbstractPostPydanticModel,
    ],
    AbstractDefaultSQLAlchemyRead[
        AbstractSQLAlchemyModel,
        AbstractID,
        AbstractDefaultPydanticModel,
        AbstractGetPydanticModel,
    ],
    AbstractDefaultSQLAlchemyUpdate[
        AbstractSQLAlchemyModel,
        AbstractID,
        AbstractDefaultPydanticModel,
        AbstractPatchPydanticModel
    ],
    AbstractDefaultSQLAlchemyDelete[
        AbstractSQLAlchemyModel,
        AbstractID,
        AbstractDefaultPydanticModel,
        AbstractDeletePydanticModel
    ],
    AbstractDefaultSQLAlchemyReadPagginated[
        AbstractSQLAlchemyModel,
        AbstractID,
        AbstractDefaultPydanticModel,
        AbstractGetPagginatedPydanticModel,
        AbstractDefaultPagginatedPydanticModel
    ]
):
    pass


class AbstractIntSQLAlchemyCRUDP(
    Generic[
        AbstractSQLAlchemyModel,
        AbstractDefaultPydanticModel,
        AbstractPostPydanticModel,
        AbstractGetPydanticModel,
        AbstractPatchPydanticModel,
        AbstractDeletePydanticModel,
        AbstractIntPaggination
    ],
    AbstractDefaultSQLAlchemyCRUDP[
        AbstractSQLAlchemyModel,
        int,
        AbstractDefaultPydanticModel,
        AbstractPostPydanticModel,
        AbstractGetPydanticModel,
        AbstractPatchPydanticModel,
        AbstractDeletePydanticModel,
        IntReadPagginationBaseModel,
        AbstractIntPaggination
    ],
    AbstractIntSQLAlchemyReadPagginated[
        AbstractSQLAlchemyModel,
        IntReadPagginationBaseModel,
        AbstractIntPaggination
    ]
):
    pass


class AbstractUUIDSQLAlchemyCRDP(
    Generic[
        AbstractSQLAlchemyModel,
        AbstractDefaultPydanticModel,
        AbstractPostPydanticModel,
        AbstractGetPydanticModel,
        AbstractDeletePydanticModel,
        AbstractUUIDPaggination
    ],
    AbstractDefaultSQLAlchemyCRDP[
        AbstractSQLAlchemyModel,
        UUID,
        AbstractDefaultPydanticModel,
        AbstractPostPydanticModel,
        AbstractGetPydanticModel,
        AbstractDeletePydanticModel,
        UUIDReadPagginationBaseModel,
        AbstractUUIDPaggination
    ],
    AbstractUUIDSQLAlchemyReadPagginated[
        AbstractSQLAlchemyModel,
        UUIDReadPagginationBaseModel,
        AbstractUUIDPaggination
    ]
):
    pass


class AbstractUUIDSQLAlchemyCRUDP(
    Generic[
        AbstractSQLAlchemyModel,
        AbstractDefaultPydanticModel,
        AbstractPostPydanticModel,
        AbstractGetPydanticModel,
        AbstractPatchPydanticModel,
        AbstractDeletePydanticModel,
        AbstractUUIDPaggination
    ],
    AbstractDefaultSQLAlchemyCRUDP[
        AbstractSQLAlchemyModel,
        UUID,
        AbstractDefaultPydanticModel,
        AbstractPostPydanticModel,
        AbstractGetPydanticModel,
        AbstractPatchPydanticModel,
        AbstractDeletePydanticModel,
        UUIDReadPagginationBaseModel,
        AbstractUUIDPaggination
    ],
    AbstractUUIDSQLAlchemyReadPagginated[
        AbstractSQLAlchemyModel,
        UUIDReadPagginationBaseModel,
        AbstractUUIDPaggination
    ]
):
    pass

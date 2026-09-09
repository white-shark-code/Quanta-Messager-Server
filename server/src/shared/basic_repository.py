from abc import abstractmethod
from typing import Generic, TypeVar
from uuid import UUID

from sqlalchemy import Select, func, select

from .abstract_repository import (
    AbstractAsyncRepoCreate,
    AbstractAsyncRepoDelete,
    AbstractAsyncRepoRead,
    AbstractAsyncRepoReadPaginated,
    AbstractAsyncRepoUpdate,
    AbstractDefaultPagginatedPydanticModel,
    AbstractDefaultPydanticModel,
    AbstractDeletePydanticModel,
    AbstractGetPagginatedPydanticModel,
    AbstractGetPydanticModel,
    AbstractPatchPydanticModel,
    AbstractPostPydanticModel,
)
from .abstract_schemas import (
    AbstractID,
    AbstractIntPagginationBaseModel,
    AbstractUUIDPagginationBaseModel,
)
from .abstract_sqlalchemy_repository import (
    AbstractDefaultSQLAlchemyAsyncRepository,
    AbstractSQLAlchemyModel,
    AbstractSQLAlchemyModelWithPrimaryInt,
    AbstractSQLAlchemyModelWithPrimaryUUID,
)
from .basic_schemas import IntGetPagginationBaseModel, UUIDGetPagginationBaseModel


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
        AbstractDefaultPydanticModel,
        AbstractSQLAlchemyModel,
    ],
):
    async def _post(
        self, post_schema: AbstractPostPydanticModel
    ) -> AbstractSQLAlchemyModel:
        new = self._model(  # type: ignore[call-arg]
            **post_schema.model_dump()
        )
        self._session.add(new)
        await self._session.refresh(new)
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
        AbstractGetPydanticModel,
        AbstractSQLAlchemyModel,
    ],
):
    async def _get(
        self, get_schema: AbstractGetPydanticModel
    ) -> AbstractSQLAlchemyModel | None:
        return await self._session.get(self._model, get_schema.id)  # type: ignore[arg-type]


class AbstractDefaultSQLAlchemyUpdate(
    Generic[
        AbstractSQLAlchemyModel,
        AbstractID,
        AbstractDefaultPydanticModel,
        AbstractPatchPydanticModel,
    ],
    AbstractDefaultSQLAlchemyAsyncRepository[
        AbstractSQLAlchemyModel,
        AbstractID,
        AbstractDefaultPydanticModel,
    ],
    AbstractAsyncRepoUpdate[
        AbstractDefaultPydanticModel,
        AbstractPatchPydanticModel,
        AbstractSQLAlchemyModel,
    ],
):
    async def _patch(
        self, patch_schema: AbstractPatchPydanticModel
    ) -> AbstractSQLAlchemyModel:
        obj = await self._session.get(  # type: ignore[arg-type]
            self._model,  # type: ignore[arg-type]
            patch_schema.id,
        )
        update_data = patch_schema.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(obj, key, value)
        await self._session.refresh(obj)
        return obj  # type: ignore[return-value]


class AbstractDefaultSQLAlchemyDelete(
    Generic[
        AbstractSQLAlchemyModel,
        AbstractID,
        AbstractDefaultPydanticModel,
        AbstractDeletePydanticModel,
    ],
    AbstractDefaultSQLAlchemyAsyncRepository[
        AbstractSQLAlchemyModel,
        AbstractID,
        AbstractDefaultPydanticModel,
    ],
    AbstractAsyncRepoDelete[
        AbstractDefaultPydanticModel,
        AbstractDeletePydanticModel,
        AbstractSQLAlchemyModel,
    ],
):
    async def _delete(
        self, delete_schema: AbstractDeletePydanticModel
    ) -> AbstractSQLAlchemyModel:
        obj = await self._session.get(  # type: ignore[arg-type]
            self._model,  # type: ignore[arg-type]
            delete_schema.id,
        )
        await self._session.delete(obj)  # type: ignore[arg-type]
        await self._session.flush()
        return obj  # type: ignore[return-value]


class AbstractDefaultSQLAlchemyReadPaginated(
    Generic[
        AbstractSQLAlchemyModel,
        AbstractID,
        AbstractDefaultPydanticModel,
        AbstractGetPagginatedPydanticModel,
        AbstractDefaultPagginatedPydanticModel,
    ],
    AbstractDefaultSQLAlchemyAsyncRepository[
        AbstractSQLAlchemyModel,
        AbstractID,
        AbstractDefaultPydanticModel,
    ],
    AbstractAsyncRepoReadPaginated[
        AbstractID,
        AbstractGetPagginatedPydanticModel,
        AbstractDefaultPagginatedPydanticModel,
        AbstractSQLAlchemyModel,
    ],
):
    @abstractmethod
    def _get_many_stmt(self, get_schema: AbstractGetPagginatedPydanticModel) -> Select:
        pass

    def _prepair_get_many_stmt(
        self, get_schema: AbstractGetPagginatedPydanticModel
    ) -> Select:
        return self._get_many_stmt(get_schema)

    async def _get_many(
        self, get_schema: AbstractGetPagginatedPydanticModel
    ) -> list[AbstractSQLAlchemyModel]:
        stmt = self._prepair_get_many_stmt(get_schema)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def _get_count(self, get_schema: AbstractGetPagginatedPydanticModel) -> int:
        stmt = self._get_many_stmt(get_schema)
        count_stmt = select(func.count()).select_from(stmt.subquery())
        count_result = await self._session.execute(count_stmt)
        return count_result.scalar_one()

    async def get_many(
        self, get_schema: AbstractGetPagginatedPydanticModel
    ) -> AbstractDefaultPagginatedPydanticModel:
        await self._before_get_many()
        data = await self._get_prepaired_dict(get_schema)
        return self._pagginated_output_pyd_model.model_validate(data)


AbstractIntPaggination = TypeVar(
    "AbstractIntPaggination", bound=AbstractIntPagginationBaseModel
)


class AbstractIntSQLAlchemyReadPagginated(
    Generic[
        AbstractSQLAlchemyModelWithPrimaryInt,
        AbstractIntPaggination,
        AbstractDefaultPydanticModel,
    ],
    AbstractDefaultSQLAlchemyReadPaginated[
        AbstractSQLAlchemyModelWithPrimaryInt,
        int,
        AbstractDefaultPydanticModel,
        IntGetPagginationBaseModel,
        AbstractIntPaggination,
    ],
):
    def _prepair_get_many_stmt(self, get_schema: IntGetPagginationBaseModel) -> Select:
        stmt: Select = self._get_many_stmt(get_schema)
        return stmt.order_by(self._model.id)  # type: ignore[arg-type]

    async def _get_prepaired_dict(
        self, get_schema: IntGetPagginationBaseModel
    ) -> dict[str, int | list[AbstractSQLAlchemyModelWithPrimaryInt] | None]:
        prepaired_dict = await super()._get_prepaired_dict(get_schema)
        items = prepaired_dict["items"]
        prepaired_dict["last_id"] = items[-1].id if items else None  # type: ignore[union-attr]
        return prepaired_dict  # type: ignore[return-value]


AbstractUUIDPaggination = TypeVar(
    "AbstractUUIDPaggination", bound=AbstractUUIDPagginationBaseModel
)


class AbstractUUIDSQLAlchemyReadPaginated(
    Generic[
        AbstractSQLAlchemyModelWithPrimaryUUID,
        AbstractUUIDPaggination,
        AbstractDefaultPydanticModel,
    ],
    AbstractDefaultSQLAlchemyReadPaginated[
        AbstractSQLAlchemyModelWithPrimaryUUID,
        UUID,
        AbstractDefaultPydanticModel,
        UUIDGetPagginationBaseModel,
        AbstractUUIDPaggination,
    ],
):
    def _prepair_get_many_stmt(self, get_schema: UUIDGetPagginationBaseModel) -> Select:
        stmt: Select = self._get_many_stmt(get_schema)
        return stmt.order_by(self._model.id)  # type: ignore[arg-type]

    async def _get_prepaired_dict(
        self, get_schema: UUIDGetPagginationBaseModel
    ) -> dict[str, int | list[AbstractSQLAlchemyModelWithPrimaryUUID] | UUID | None]:
        prepaired_dict = await super()._get_prepaired_dict(get_schema)
        items = prepaired_dict["items"]
        prepaired_dict["last_id"] = items[-1].id if items else None  # type: ignore[union-attr]
        return prepaired_dict  # type: ignore[return-value]


class AbstractDefaultSQLAlchemyCRP(
    Generic[
        AbstractSQLAlchemyModel,
        AbstractID,
        AbstractDefaultPydanticModel,
        AbstractPostPydanticModel,
        AbstractGetPydanticModel,
        AbstractGetPagginatedPydanticModel,
        AbstractDefaultPagginatedPydanticModel,
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
    AbstractDefaultSQLAlchemyReadPaginated[
        AbstractSQLAlchemyModel,
        AbstractID,
        AbstractDefaultPydanticModel,
        AbstractGetPagginatedPydanticModel,
        AbstractDefaultPagginatedPydanticModel,
    ],
):
    pass


class AbstractDefaultSQLAlchemyCRDP(
    Generic[
        AbstractSQLAlchemyModel,
        AbstractID,
        AbstractDefaultPydanticModel,
        AbstractPostPydanticModel,
        AbstractGetPydanticModel,
        AbstractDeletePydanticModel,
        AbstractGetPagginatedPydanticModel,
        AbstractDefaultPagginatedPydanticModel,
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
        AbstractDeletePydanticModel,
    ],
    AbstractDefaultSQLAlchemyReadPaginated[
        AbstractSQLAlchemyModel,
        AbstractID,
        AbstractDefaultPydanticModel,
        AbstractGetPagginatedPydanticModel,
        AbstractDefaultPagginatedPydanticModel,
    ],
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
        AbstractDefaultPagginatedPydanticModel,
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
        AbstractPatchPydanticModel,
    ],
    AbstractDefaultSQLAlchemyDelete[
        AbstractSQLAlchemyModel,
        AbstractID,
        AbstractDefaultPydanticModel,
        AbstractDeletePydanticModel,
    ],
    AbstractDefaultSQLAlchemyReadPaginated[
        AbstractSQLAlchemyModel,
        AbstractID,
        AbstractDefaultPydanticModel,
        AbstractGetPagginatedPydanticModel,
        AbstractDefaultPagginatedPydanticModel,
    ],
):
    pass


class AbstractIntSQLAlchemyCRUDP(
    Generic[
        AbstractSQLAlchemyModelWithPrimaryInt,
        AbstractDefaultPydanticModel,
        AbstractPostPydanticModel,
        AbstractGetPydanticModel,
        AbstractPatchPydanticModel,
        AbstractDeletePydanticModel,
        AbstractIntPaggination,
    ],
    AbstractDefaultSQLAlchemyCRUDP[
        AbstractSQLAlchemyModelWithPrimaryInt,
        int,
        AbstractDefaultPydanticModel,
        AbstractPostPydanticModel,
        AbstractGetPydanticModel,
        AbstractPatchPydanticModel,
        AbstractDeletePydanticModel,
        IntGetPagginationBaseModel,
        AbstractIntPaggination,
    ],
    AbstractIntSQLAlchemyReadPagginated[
        AbstractSQLAlchemyModelWithPrimaryInt,
        AbstractIntPaggination,
        AbstractDefaultPydanticModel,
    ],
):
    pass


class AbstractUUIDSQLAlchemyCRSpecialPagination(
    Generic[
        AbstractSQLAlchemyModelWithPrimaryUUID,
        AbstractDefaultPydanticModel,
        AbstractPostPydanticModel,
        AbstractGetPydanticModel,
        AbstractUUIDPaggination,
    ],
    AbstractDefaultSQLAlchemyCRP[
        AbstractSQLAlchemyModelWithPrimaryUUID,
        UUID,
        AbstractDefaultPydanticModel,
        AbstractPostPydanticModel,
        AbstractGetPydanticModel,
        UUIDGetPagginationBaseModel,
        AbstractUUIDPaggination,
    ],
    AbstractUUIDSQLAlchemyReadPaginated[
        AbstractSQLAlchemyModelWithPrimaryUUID,
        AbstractUUIDPaggination,
        AbstractDefaultPydanticModel,
    ],
):
    pass


class AbstractUUIDSQLAlchemyCRUDP(
    Generic[
        AbstractSQLAlchemyModelWithPrimaryUUID,
        AbstractDefaultPydanticModel,
        AbstractPostPydanticModel,
        AbstractGetPydanticModel,
        AbstractPatchPydanticModel,
        AbstractDeletePydanticModel,
        AbstractUUIDPaggination,
    ],
    AbstractDefaultSQLAlchemyCRUDP[
        AbstractSQLAlchemyModelWithPrimaryUUID,
        UUID,
        AbstractDefaultPydanticModel,
        AbstractPostPydanticModel,
        AbstractGetPydanticModel,
        AbstractPatchPydanticModel,
        AbstractDeletePydanticModel,
        UUIDGetPagginationBaseModel,
        AbstractUUIDPaggination,
    ],
    AbstractUUIDSQLAlchemyReadPaginated[
        AbstractSQLAlchemyModelWithPrimaryUUID,
        AbstractUUIDPaggination,
        AbstractDefaultPydanticModel,
    ],
):
    pass


class AbstractUUIDSQLAlchemyCRP(
    Generic[
        AbstractSQLAlchemyModelWithPrimaryUUID,
        AbstractDefaultPydanticModel,
        AbstractPostPydanticModel,
        AbstractGetPydanticModel,
        AbstractUUIDPaggination,
    ],
    AbstractDefaultSQLAlchemyCRP[
        AbstractSQLAlchemyModelWithPrimaryUUID,
        UUID,
        AbstractDefaultPydanticModel,
        AbstractPostPydanticModel,
        AbstractGetPydanticModel,
        UUIDGetPagginationBaseModel,
        AbstractUUIDPaggination,
    ],
    AbstractUUIDSQLAlchemyReadPaginated[
        AbstractSQLAlchemyModelWithPrimaryUUID,
        AbstractUUIDPaggination,
        AbstractDefaultPydanticModel,
    ],
):
    pass


class AbstractUUIDSQLAlchemyCRDP(
    Generic[
        AbstractSQLAlchemyModelWithPrimaryUUID,
        AbstractDefaultPydanticModel,
        AbstractPostPydanticModel,
        AbstractGetPydanticModel,
        AbstractDeletePydanticModel,
        AbstractUUIDPaggination,
    ],
    AbstractDefaultSQLAlchemyCRDP[
        AbstractSQLAlchemyModelWithPrimaryUUID,
        UUID,
        AbstractDefaultPydanticModel,
        AbstractPostPydanticModel,
        AbstractGetPydanticModel,
        AbstractDeletePydanticModel,
        UUIDGetPagginationBaseModel,
        AbstractUUIDPaggination,
    ],
    AbstractUUIDSQLAlchemyReadPaginated[
        AbstractSQLAlchemyModelWithPrimaryUUID,
        AbstractUUIDPaggination,
        AbstractDefaultPydanticModel,
    ],
):
    pass

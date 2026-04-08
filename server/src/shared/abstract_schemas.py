from typing import (
    TypeVar,
    Generic,
    Any
)
from pydantic import BaseModel, ConfigDict
from uuid import UUID


AbstractID = TypeVar(
    'AbstractID'
)

class AbstractBaseModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class AbstractReadBaseModel(
    BaseModel,
    Generic[
        AbstractID
    ]
):
    id: AbstractID


class AbstractCreateBaseModel(BaseModel):
    pass


class AbstractUpdateBaseModel(
    AbstractReadBaseModel[
        AbstractID
    ]
):
    pass


class AbstractDeleteBaseModel(
    AbstractReadBaseModel[
        AbstractID
    ]
):
    pass


class AbstractDefaultBaseModel(
    AbstractReadBaseModel[
        AbstractID
    ]
):
    pass


class AbstractPagginationBaseModel(
    BaseModel
):
    page_size: int


class AbstractDefaultReadPagginationBaseModel(
    AbstractPagginationBaseModel,
    Generic[
        AbstractID
    ]
):
    last_id: AbstractID | None


AbstractItem = TypeVar('AbstractItem', bound=Any)


class AbstractDefaultPagginationBaseModel(
    AbstractPagginationBaseModel,
    Generic[
        AbstractID,
        AbstractItem
    ]
):
    count_pages: int
    items: list[AbstractItem]
    last_id: AbstractID


class AbstractIntPagginationBaseModel(
    AbstractDefaultPagginationBaseModel[
        int,
        AbstractItem
    ]
):
    pass


class AbstractUUIDPagginationBaseModel(
    AbstractDefaultPagginationBaseModel[
        UUID,
        AbstractItem
    ]
):
    pass

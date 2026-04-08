from uuid import UUID
from .abstract_schemas import AbstractDefaultReadPagginationBaseModel

class IntReadPagginationBaseModel(
    AbstractDefaultReadPagginationBaseModel[
        int
    ]
):
    pass

class UUIDReadPagginationBaseModel(
    AbstractDefaultReadPagginationBaseModel[
        UUID
    ]
):
    pass

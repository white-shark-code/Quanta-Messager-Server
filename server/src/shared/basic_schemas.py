"""Concrete pagination schemas for integer and UUID primary keys.

Конкретные схемы пагинации для целочисленных и UUID первичных ключей.
"""

from uuid import UUID

from .abstract_schemas import AbstractDefaultReadPagginationBaseModel


class IntGetPagginationBaseModel(AbstractDefaultReadPagginationBaseModel[int]):
    """Pagination query schema for entities with integer IDs.

    Схема запроса пагинации для сущностей с целочисленными идентификаторами.
    """

    pass


class UUIDGetPagginationBaseModel(AbstractDefaultReadPagginationBaseModel[UUID]):
    """Pagination query schema for entities with UUID IDs.

    Схема запроса пагинации для сущностей с UUID-идентификаторами.
    """

    pass

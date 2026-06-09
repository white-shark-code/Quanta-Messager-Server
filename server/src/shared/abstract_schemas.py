"""Abstract Pydantic schemas for the repository and facade layers.

This module provides base Pydantic models that define common patterns
for CRUD operations, pagination, and data transfer objects.
Concrete schemas should inherit from these base classes.

Абстрактные Pydantic-схемы для слоёв репозиториев и фасадов.

Модуль предоставляет базовые Pydantic-модели, определяющие общие паттерны
для CRUD-операций, пагинации и объектов передачи данных.
Конкретные схемы должны наследовать эти базовые классы.
"""

from typing import Any, Generic, TypeVar
from uuid import UUID

from pydantic import BaseModel, ConfigDict

AbstractID = TypeVar("AbstractID")


class AbstractBaseModel(BaseModel):
    """Base Pydantic model with ORM compatibility enabled.

    Базовая Pydantic-модель с поддержкой совместимости с ORM.
    """

    model_config = ConfigDict(from_attributes=True)


class AbstractReadBaseModel(BaseModel, Generic[AbstractID]):
    """Base schema for read operations requiring an entity ID.

    Type Parameters:
        AbstractID: The type of the entity identifier (int, UUID, etc.).

    Базовая схема для операций чтения, требующих ID сущности.

    Type Parameters:
        AbstractID: Тип идентификатора сущности (int, UUID и т.д.).
    """

    id: AbstractID


class AbstractCreateBaseModel(BaseModel):
    """Base schema for create operations.

    Inherit from this class to define schemas for entity creation.

    Базовая схема для операций создания.

    Наследуйте этот класс для определения схем создания сущностей.
    """

    pass


class AbstractUpdateBaseModel(AbstractReadBaseModel[AbstractID]):
    """Base schema for update operations.

    Extends AbstractReadBaseModel to require an entity ID for updates.

    Базовая схема для операций обновления.

    Расширяет AbstractReadBaseModel, требуя ID сущности для обновления.
    """

    pass


class AbstractDeleteBaseModel(AbstractReadBaseModel[AbstractID]):
    """Base schema for delete operations.

    Extends AbstractReadBaseModel to require an entity ID for deletion.

    Базовая схема для операций удаления.

    Расширяет AbstractReadBaseModel, требуя ID сущности для удаления.
    """

    pass


class AbstractDefaultBaseModel(AbstractReadBaseModel[AbstractID]):
    """Default base schema for entity output.

    Used as the standard output model for CRUD operations.

    Стандартная базовая схема для вывода сущности.

    Используется как стандартная выходная модель для CRUD-операций.
    """

    pass


class AbstractPagginationBaseModel(BaseModel):
    """Base schema for pagination parameters.

    Базовая схема для параметров пагинации.
    """

    page_size: int


class AbstractDefaultReadPagginationBaseModel(
    AbstractPagginationBaseModel, Generic[AbstractID]
):
    """Base schema for paginated read query parameters.

    Type Parameters:
        AbstractID: The type of the entity identifier used for cursor-based pagination.

    Базовая схема для параметров постраничного запроса.

    Type Parameters:
        AbstractID: Тип идентификатора сущности для курсорной пагинации.
    """

    last_id: AbstractID | None


AbstractItem = TypeVar("AbstractItem", bound=Any)


class AbstractDefaultPagginationBaseModel(
    AbstractPagginationBaseModel, Generic[AbstractID, AbstractItem]
):
    """Base schema for paginated response data.

    Type Parameters:
        AbstractID: The type of the entity identifier.
        AbstractItem: The type of items in the paginated list.

    Базовая схема для постраничных данных ответа.

    Type Parameters:
        AbstractID: Тип идентификатора сущности.
        AbstractItem: Тип элементов в постраничном списке.
    """

    count_pages: int
    items: list[AbstractItem]
    last_id: AbstractID


class AbstractIntPagginationBaseModel(
    AbstractDefaultPagginationBaseModel[int, AbstractItem]
):
    """Pagination response schema with integer IDs.

    Схема постраничного ответа с целочисленными идентификаторами.
    """

    pass


class AbstractUUIDPagginationBaseModel(
    AbstractDefaultPagginationBaseModel[UUID, AbstractItem]
):
    """Pagination response schema with UUID IDs.

    Схема постраничного ответа с UUID-идентификаторами.
    """

    pass

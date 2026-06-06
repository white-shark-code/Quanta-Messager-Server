"""Abstract facade classes for business logic orchestration.

This module implements the Facade pattern to separate business logic
from data access. Facades wrap repositories and provide a clean API
for service layers, including pre/post processing hooks.

Абстрактные классы фасадных компонентов для оркестрации бизнес-логики.

Данный модуль реализует паттерн «Фасад» для разделения бизнес-логики
и доступа к данным. Фасады оборачивают репозитории и предоставляют
чистый API для слоёв сервисов, включая хуки предварительной
и последующей обработки.
"""

from abc import ABC
from typing import Any, Generic, TypeVar

from sqlalchemy.ext.asyncio import AsyncSession

from authentication.models import User

from .abstract_repository import GenericAsyncRepo
from .abstract_schemas import (
    AbstractCreateBaseModel,
    AbstractDefaultBaseModel,
    AbstractDefaultPagginationBaseModel,
    AbstractDefaultReadPagginationBaseModel,
    AbstractDeleteBaseModel,
    AbstractReadBaseModel,
    AbstractUpdateBaseModel,
)

AbstractRepo = TypeVar("AbstractRepo", bound=GenericAsyncRepo)

AbstractDefaultPydanticModel = TypeVar(
    "AbstractDefaultPydanticModel", bound=AbstractDefaultBaseModel
)
AbstractPostPydanticModel = TypeVar(
    "AbstractPostPydanticModel", bound=AbstractCreateBaseModel
)
AbstractGetPydanticModel = TypeVar(
    "AbstractGetPydanticModel", bound=AbstractReadBaseModel
)
AbstractPatchPydanticModel = TypeVar(
    "AbstractPatchPydanticModel", bound=AbstractUpdateBaseModel
)
AbstractDeletePydanticModel = TypeVar(
    "AbstractDeletePydanticModel", bound=AbstractDeleteBaseModel
)
AbstractGetPagginatedPydanticModel = TypeVar(
    "AbstractGetPagginatedPydanticModel", bound=AbstractDefaultReadPagginationBaseModel
)
AbstractDefaultPagginatedPydanticModel = TypeVar(
    "AbstractDefaultPagginatedPydanticModel", bound=AbstractDefaultPagginationBaseModel
)


class AbstractFacadeBase(Generic[AbstractRepo], ABC):
    """Base facade class that initializes the repository and stores context.

    Базовый класс фасада, который инициализирует репозиторий
    и хранит контекст.
    """

    def __init__(self, repo_class: type[AbstractRepo], user: Any, session: Any):
        """Initialize the facade.

        Args:
            repo_class: The repository class to instantiate.
            user: The authenticated user context.
            session: The database session.

        Инициализирует фасад.

        Args:
            repo_class: Класс репозитория для создания экземпляра.
            user: Контекст аутентифицированного пользователя.
            session: Сессия базы данных.
        """
        self._repo = repo_class(session=session, user=user)
        self.__user = user
        self.__session = session

    @property
    def _session(self) -> AsyncSession:
        """Return the async database session.

        Возвращает асинхронную сессию базы данных.
        """
        return self.__session

    @property
    def _user(self) -> User:
        """Return the authenticated user context.

        Возвращает контекст аутентифицированного пользователя.
        """
        return self.__user


class AbstractFacadeCreate(
    Generic[AbstractRepo, AbstractDefaultPydanticModel, AbstractPostPydanticModel],
    AbstractFacadeBase[AbstractRepo],
    ABC,
):
    """Mixin facade for create operations with pre/post hooks.

    Фасадный миксин для операций создания с хуками предварительной
    и последующей обработки.
    """

    async def _before_create(
        self, schema: AbstractPostPydanticModel
    ) -> AbstractPostPydanticModel:
        """Hook called before creating an entity. Override for custom logic.

        Args:
            schema: The validated create schema.

        Returns:
            The (possibly modified) create schema.

        Хук, вызываемый перед созданием сущности.
        Переопределите для пользовательской логики.

        Args:
            schema: Валидированная схема создания.

        Returns:
            (Возможно изменённая) схема создания.
        """
        return schema

    async def _after_create(self, result: AbstractDefaultPydanticModel) -> None:
        """Hook called after creating an entity. Override for side effects.

        Args:
            result: The created entity.

        Хук, вызываемый после создания сущности.
        Переопределите для побочных эффектов.

        Args:
            result: Созданная сущность.
        """
        pass

    async def create(
        self, schema: AbstractPostPydanticModel
    ) -> AbstractDefaultPydanticModel:
        """Create a new entity with pre/post processing.

        Args:
            schema: The validated create schema.

        Returns:
            The created entity.

        Создание новой сущности с предварительной и последующей обработкой.

        Args:
            schema: Валидированная схема создания.

        Returns:
            Созданная сущность.
        """
        schema = await self._before_create(schema)
        result = await self._repo.post(post_schema=schema)
        await self._after_create(result)
        return result


class AbstractFacadeRead(
    Generic[AbstractRepo, AbstractDefaultPydanticModel, AbstractGetPydanticModel],
    AbstractFacadeBase[AbstractRepo],
    ABC,
):
    """Mixin facade for read operations with pre/post hooks.

    Фасадный миксин для операций чтения с хуками предварительной
    и последующей обработки.
    """

    async def _before_read(
        self, schema: AbstractGetPydanticModel
    ) -> AbstractGetPydanticModel:
        """Hook called before reading an entity.

        Args:
            schema: The validated read schema.

        Returns:
            The (possibly modified) read schema.

        Хук, вызываемый перед чтением сущности.

        Args:
            schema: Валидированная схема чтения.

        Returns:
            (Возможно изменённая) схема чтения.
        """
        return schema

    async def _after_read(self, result: AbstractDefaultPydanticModel) -> None:
        """Hook called after reading an entity.

        Args:
            result: The retrieved entity.

        Хук, вызываемый после чтения сущности.

        Args:
            result: Извлечённая сущность.
        """
        pass

    async def read(
        self, schema: AbstractGetPydanticModel
    ) -> AbstractDefaultPydanticModel:
        """Read an entity with pre/post processing.

        Args:
            schema: The validated read schema.

        Returns:
            The retrieved entity.

        Чтение сущности с предварительной и последующей обработкой.

        Args:
            schema: Валидированная схема чтения.

        Returns:
            Извлечённая сущность.
        """
        schema = await self._before_read(schema)
        result = await self._repo.get(get_schema=schema)
        await self._after_read(result)
        return result


class AbstractFacadeUpdate(
    Generic[AbstractRepo, AbstractDefaultPydanticModel, AbstractPatchPydanticModel],
    AbstractFacadeBase[AbstractRepo],
    ABC,
):
    """Mixin facade for update operations with pre/post hooks.

    Фасадный миксин для операций обновления с хуками предварительной
    и последующей обработки.
    """

    async def _before_update(
        self, schema: AbstractPatchPydanticModel
    ) -> AbstractPatchPydanticModel:
        """Hook called before updating an entity.

        Args:
            schema: The validated update schema.

        Returns:
            The (possibly modified) update schema.

        Хук, вызываемый перед обновлением сущности.

        Args:
            schema: Валидированная схема обновления.

        Returns:
            (Возможно изменённая) схема обновления.
        """
        return schema

    async def _after_update(self, result: AbstractDefaultPydanticModel) -> None:
        """Hook called after updating an entity.

        Args:
            result: The updated entity.

        Хук, вызываемый после обновления сущности.

        Args:
            result: Обновлённая сущность.
        """
        pass

    async def update(
        self, schema: AbstractPatchPydanticModel
    ) -> AbstractDefaultPydanticModel:
        """Update an entity with pre/post processing.

        Args:
            schema: The validated update schema.

        Returns:
            The updated entity.

        Обновление сущности с предварительной и последующей обработкой.

        Args:
            schema: Валидированная схема обновления.

        Returns:
            Обновлённая сущность.
        """
        schema = await self._before_update(schema)
        result = await self._repo.patch(patch_schema=schema)
        await self._after_update(result)
        return result


class AbstractFacadeDelete(
    Generic[AbstractRepo, AbstractDefaultPydanticModel, AbstractDeletePydanticModel],
    AbstractFacadeBase[AbstractRepo],
    ABC,
):
    """Mixin facade for delete operations with pre/post hooks.

    Фасадный миксин для операций удаления с хуками предварительной
    и последующей обработки.
    """

    async def _before_delete(
        self, schema: AbstractDeletePydanticModel
    ) -> AbstractDeletePydanticModel:
        """Hook called before deleting an entity.

        Args:
            schema: The validated delete schema.

        Returns:
            The (possibly modified) delete schema.

        Хук, вызываемый перед удалением сущности.

        Args:
            schema: Валидированная схема удаления.

        Returns:
            (Возможно изменённая) схема удаления.
        """
        return schema

    async def _after_delete(self, result: AbstractDefaultPydanticModel) -> None:
        """Hook called after deleting an entity.

        Args:
            result: The deleted entity.

        Хук, вызываемый после удаления сущности.

        Args:
            result: Удалённая сущность.
        """
        pass

    async def delete(
        self, schema: AbstractDeletePydanticModel
    ) -> AbstractDefaultPydanticModel:
        """Delete an entity with pre/post processing.

        Args:
            schema: The validated delete schema.

        Returns:
            The deleted entity.

        Удаление сущности с предварительной и последующей обработкой.

        Args:
            schema: Валидированная схема удаления.

        Returns:
            Удалённая сущность.
        """
        schema = await self._before_delete(schema)
        result = await self._repo.delete(delete_schema=schema)
        await self._after_delete(result)
        return result


class AbstractFacadeReadPaginated(
    Generic[
        AbstractRepo,
        AbstractDefaultPagginatedPydanticModel,
        AbstractGetPagginatedPydanticModel,
    ],
    AbstractFacadeBase[AbstractRepo],
    ABC,
):
    """Mixin facade for paginated read operations with pre/post hooks.

    Фасадный миксин для операций постраничного чтения с хуками
    предварительной и последующей обработки.
    """

    async def _before_read_paginated(
        self, schema: AbstractGetPagginatedPydanticModel
    ) -> AbstractGetPagginatedPydanticModel:
        """Hook called before reading paginated entities.

        Args:
            schema: The validated pagination query schema.

        Returns:
            The (possibly modified) pagination query schema.

        Хук, вызываемый перед чтением постраничных сущностей.

        Args:
            schema: Валидированная схема запроса пагинации.

        Returns:
            (Возможно изменённая) схема запроса пагинации.
        """
        return schema

    async def _after_read_paginated(
        self, result: AbstractDefaultPagginatedPydanticModel
    ) -> None:
        """Hook called after reading paginated entities.

        Args:
            result: The paginated result.

        Хук, вызываемый после чтения постраничных сущностей.

        Args:
            result: Результат пагинации.
        """
        pass

    async def read_paginated(
        self, schema: AbstractGetPagginatedPydanticModel
    ) -> AbstractDefaultPagginatedPydanticModel:
        """Read paginated entities with pre/post processing.

        Args:
            schema: The validated pagination query schema.

        Returns:
            The paginated result.

        Чтение постраничных сущностей с предварительной и последующей обработкой.

        Args:
            schema: Валидированная схема запроса пагинации.

        Returns:
            Результат пагинации.
        """
        schema = await self._before_read_paginated(schema)
        result = await self._repo.get_many(get_schema=schema)
        await self._after_read_paginated(result)
        return result


# --- Комбинации Фасадов ---


class AbstractFacadeCR(
    Generic[
        AbstractRepo,
        AbstractDefaultPydanticModel,
        AbstractPostPydanticModel,
        AbstractGetPydanticModel,
    ],
    AbstractFacadeCreate[
        AbstractRepo, AbstractDefaultPydanticModel, AbstractPostPydanticModel
    ],
    AbstractFacadeRead[
        AbstractRepo, AbstractDefaultPydanticModel, AbstractGetPydanticModel
    ],
    ABC,
):
    """Combination facade supporting Create and Read operations.

    Комбинированный фасад, поддерживающий операции создания и чтения.
    """

    pass


class AbstractFacadeCRU(
    Generic[
        AbstractRepo,
        AbstractDefaultPydanticModel,
        AbstractPostPydanticModel,
        AbstractGetPydanticModel,
        AbstractPatchPydanticModel,
    ],
    AbstractFacadeCreate[
        AbstractRepo, AbstractDefaultPydanticModel, AbstractPostPydanticModel
    ],
    AbstractFacadeRead[
        AbstractRepo, AbstractDefaultPydanticModel, AbstractGetPydanticModel
    ],
    AbstractFacadeUpdate[
        AbstractRepo, AbstractDefaultPydanticModel, AbstractPatchPydanticModel
    ],
    ABC,
):
    """Combination facade supporting Create, Read, and Update operations.

    Комбинированный фасад, поддерживающий операции создания, чтения
    и обновления.
    """

    pass


class AbstractFacadeCRD(
    Generic[
        AbstractRepo,
        AbstractDefaultPydanticModel,
        AbstractPostPydanticModel,
        AbstractGetPydanticModel,
        AbstractDeletePydanticModel,
    ],
    AbstractFacadeCreate[
        AbstractRepo, AbstractDefaultPydanticModel, AbstractPostPydanticModel
    ],
    AbstractFacadeRead[
        AbstractRepo, AbstractDefaultPydanticModel, AbstractGetPydanticModel
    ],
    AbstractFacadeDelete[
        AbstractRepo, AbstractDefaultPydanticModel, AbstractDeletePydanticModel
    ],
    ABC,
):
    """Combination facade supporting Create, Read, and Delete operations.

    Комбинированный фасад, поддерживающий операции создания, чтения
    и удаления.
    """

    pass


class AbstractFacadeRUD(
    Generic[
        AbstractRepo,
        AbstractDefaultPydanticModel,
        AbstractGetPydanticModel,
        AbstractPatchPydanticModel,
        AbstractDeletePydanticModel,
    ],
    AbstractFacadeRead[
        AbstractRepo, AbstractDefaultPydanticModel, AbstractGetPydanticModel
    ],
    AbstractFacadeUpdate[
        AbstractRepo, AbstractDefaultPydanticModel, AbstractPatchPydanticModel
    ],
    AbstractFacadeDelete[
        AbstractRepo, AbstractDefaultPydanticModel, AbstractDeletePydanticModel
    ],
    ABC,
):
    """Combination facade supporting Read, Update, and Delete operations.

    Комбинированный фасад, поддерживающий операции чтения, обновления
    и удаления.
    """

    pass


class AbstractFacadeCRUD(
    Generic[
        AbstractRepo,
        AbstractDefaultPydanticModel,
        AbstractPostPydanticModel,
        AbstractGetPydanticModel,
        AbstractPatchPydanticModel,
        AbstractDeletePydanticModel,
    ],
    AbstractFacadeCreate[
        AbstractRepo, AbstractDefaultPydanticModel, AbstractPostPydanticModel
    ],
    AbstractFacadeRead[
        AbstractRepo, AbstractDefaultPydanticModel, AbstractGetPydanticModel
    ],
    AbstractFacadeUpdate[
        AbstractRepo, AbstractDefaultPydanticModel, AbstractPatchPydanticModel
    ],
    AbstractFacadeDelete[
        AbstractRepo, AbstractDefaultPydanticModel, AbstractDeletePydanticModel
    ],
    ABC,
):
    """Combination facade supporting full CRUD operations.

    Комбинированный фасад, поддерживающий полный набор CRUD-операций.
    """

    pass


class AbstractFacadeCRUP(
    Generic[
        AbstractRepo,
        AbstractDefaultPydanticModel,
        AbstractPostPydanticModel,
        AbstractGetPydanticModel,
        AbstractPatchPydanticModel,
        AbstractGetPagginatedPydanticModel,
        AbstractDefaultPagginatedPydanticModel,
    ],
    AbstractFacadeCreate[
        AbstractRepo, AbstractDefaultPydanticModel, AbstractPostPydanticModel
    ],
    AbstractFacadeRead[
        AbstractRepo, AbstractDefaultPydanticModel, AbstractGetPydanticModel
    ],
    AbstractFacadeUpdate[
        AbstractRepo, AbstractDefaultPydanticModel, AbstractPatchPydanticModel
    ],
    AbstractFacadeReadPaginated[
        AbstractRepo,
        AbstractDefaultPagginatedPydanticModel,
        AbstractGetPagginatedPydanticModel,
    ],
    ABC,
):
    """Combination facade supporting Create, Read,
    Update, and Paginated Read operations.

    Комбинированный фасад, поддерживающий операции создания, чтения,
    обновления и постраничного чтения.
    """

    pass


class AbstractFacadeCRDP(
    Generic[
        AbstractRepo,
        AbstractDefaultPydanticModel,
        AbstractPostPydanticModel,
        AbstractGetPydanticModel,
        AbstractDeletePydanticModel,
        AbstractGetPagginatedPydanticModel,
        AbstractDefaultPagginatedPydanticModel,
    ],
    AbstractFacadeCreate[
        AbstractRepo, AbstractDefaultPydanticModel, AbstractPostPydanticModel
    ],
    AbstractFacadeRead[
        AbstractRepo, AbstractDefaultPydanticModel, AbstractGetPydanticModel
    ],
    AbstractFacadeDelete[
        AbstractRepo, AbstractDefaultPydanticModel, AbstractDeletePydanticModel
    ],
    AbstractFacadeReadPaginated[
        AbstractRepo,
        AbstractDefaultPagginatedPydanticModel,
        AbstractGetPagginatedPydanticModel,
    ],
    ABC,
):
    """Combination facade supporting Create, Read,
    Delete, and Paginated Read operations.

    Комбинированный фасад, поддерживающий операции создания, чтения,
    удаления и постраничного чтения.
    """

    pass


class AbstractFacadeRUDP(
    Generic[
        AbstractRepo,
        AbstractDefaultPydanticModel,
        AbstractGetPydanticModel,
        AbstractPatchPydanticModel,
        AbstractDeletePydanticModel,
        AbstractGetPagginatedPydanticModel,
        AbstractDefaultPagginatedPydanticModel,
    ],
    AbstractFacadeRead[
        AbstractRepo, AbstractDefaultPydanticModel, AbstractGetPydanticModel
    ],
    AbstractFacadeUpdate[
        AbstractRepo, AbstractDefaultPydanticModel, AbstractPatchPydanticModel
    ],
    AbstractFacadeDelete[
        AbstractRepo, AbstractDefaultPydanticModel, AbstractDeletePydanticModel
    ],
    AbstractFacadeReadPaginated[
        AbstractRepo,
        AbstractDefaultPagginatedPydanticModel,
        AbstractGetPagginatedPydanticModel,
    ],
    ABC,
):
    """Combination facade supporting Read, Update,
    Delete, and Paginated Read operations.

    Комбинированный фасад, поддерживающий операции чтения, обновления,
    удаления и постраничного чтения.
    """

    pass


class AbstractFacadeCRUDP(
    Generic[
        AbstractRepo,
        AbstractDefaultPydanticModel,
        AbstractPostPydanticModel,
        AbstractGetPydanticModel,
        AbstractPatchPydanticModel,
        AbstractDeletePydanticModel,
        AbstractGetPagginatedPydanticModel,
        AbstractDefaultPagginatedPydanticModel,
    ],
    AbstractFacadeCreate[
        AbstractRepo, AbstractDefaultPydanticModel, AbstractPostPydanticModel
    ],
    AbstractFacadeRead[
        AbstractRepo, AbstractDefaultPydanticModel, AbstractGetPydanticModel
    ],
    AbstractFacadeUpdate[
        AbstractRepo, AbstractDefaultPydanticModel, AbstractPatchPydanticModel
    ],
    AbstractFacadeDelete[
        AbstractRepo, AbstractDefaultPydanticModel, AbstractDeletePydanticModel
    ],
    AbstractFacadeReadPaginated[
        AbstractRepo,
        AbstractDefaultPagginatedPydanticModel,
        AbstractGetPagginatedPydanticModel,
    ],
    ABC,
):
    """Combination facade supporting full CRUD plus Paginated Read operations.

    Комбинированный фасад, поддерживающий полный набор CRUD-операций
    плюс постраничное чтение.
    """

    pass

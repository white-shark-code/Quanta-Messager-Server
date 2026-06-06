"""Abstract repository interfaces for the repository pattern.

This module provides generic async repository base classes that define
contracts for CRUD operations with Pydantic model validation.
Concrete implementations should inherit from combination classes
like AbstractAsyncCRUDRepo or implement individual operation mixins.

Абстрактные интерфейсы репозиториев для паттерна Repository.

Модуль предоставляет обобщённые асинхронные базовые классы, определяющие
контракты CRUD-операций с валидацией Pydantic-моделей.
Конкретные реализации должны наследовать комбинированные классы
(например, AbstractAsyncCRUDRepo) или отдельные миксины операций.
"""

from abc import ABC, abstractmethod
from typing import (
    Generic,
    TypeVar,
)

from .abstract_schemas import (
    AbstractCreateBaseModel,
    AbstractDefaultBaseModel,
    AbstractDefaultPagginationBaseModel,
    AbstractDefaultReadPagginationBaseModel,
    AbstractDeleteBaseModel,
    AbstractID,
    AbstractReadBaseModel,
    AbstractUpdateBaseModel,
)

AbstractDefaultPydanticModel = TypeVar(
    "AbstractDefaultPydanticModel", bound=AbstractDefaultBaseModel
)
AbstractPostPydanticModel = TypeVar(
    "AbstractPostPydanticModel", bound=AbstractCreateBaseModel
)
AbstractInternalModel = TypeVar("AbstractInternalModel")


class GenericAsyncRepo(Generic[AbstractDefaultPydanticModel], ABC):
    """Base generic async repository interface.

    Defines the output Pydantic model property that all repository
    implementations must provide for response validation.

    Базовый обобщённый интерфейс асинхронного репозитория.

    Определяет свойство выходной Pydantic-модели, которое все реализации
    репозиториев должны предоставить для валидации ответов.
    """

    @property
    @abstractmethod
    def _output_pyd_model(self) -> type[AbstractDefaultPydanticModel]:
        """Return the Pydantic model class used for output validation.

        Возвращает класс Pydantic-модели для валидации выходных данных.
        """
        pass


class AbstractAsyncRepoCreate(
    Generic[
        AbstractPostPydanticModel,
        AbstractDefaultPydanticModel,
        AbstractInternalModel,
    ],
    GenericAsyncRepo[AbstractDefaultPydanticModel],
    ABC,
):
    """Mixin repository for creating (POST) operations.

    Provides a template method pattern with _before_post hook
    for pre-processing and automatic Pydantic validation of the result.

    Миксин репозитория для операций создания (POST).

    Использует паттерн Template Method с хуком _before_post
    для предварительной обработки и автоматической валидации
    результата через Pydantic.
    """

    async def _before_post(self):
        """Hook called before creating an entity. Override for custom logic.

        Хук, вызываемый перед созданием сущности. Переопределите для своей логики.
        """
        pass

    @abstractmethod
    async def _post(
        self, post_schema: AbstractPostPydanticModel
    ) -> AbstractInternalModel:
        """Perform the actual creation of an entity.

        Args:
            post_schema: Validated Pydantic model with creation data.

        Returns:
            The created entity (dict, ORM object, etc.).

        Выполняет фактическое создание сущности.

        Args:
            post_schema: Валидированная Pydantic-модель с данными создания.

        Returns:
            Созданная сущность (dict, ORM-объект и т.д.).
        """
        pass

    async def post(
        self, post_schema: AbstractPostPydanticModel
    ) -> AbstractDefaultPydanticModel:
        """Create a new entity and return validated result.

        Args:
            post_schema: Validated Pydantic model with creation data.

        Returns:
            Validated Pydantic model of the created entity.

        Создаёт новую сущность и возвращает валидированный результат.

        Args:
            post_schema: Валидированная Pydantic-модель с данными создания.

        Returns:
            Валидированная Pydantic-модель созданной сущности.
        """
        await self._before_post()
        return self._output_pyd_model.model_validate(
            await self._post(post_schema=post_schema)
        )


AbstractGetPydanticModel = TypeVar(
    "AbstractGetPydanticModel", bound=AbstractReadBaseModel
)


class AbstractAsyncRepoRead(
    Generic[
        AbstractDefaultPydanticModel,
        AbstractGetPydanticModel,
        AbstractInternalModel,
    ],
    GenericAsyncRepo[AbstractDefaultPydanticModel],
    ABC,
):
    """Mixin repository for reading (GET) a single entity.

    Uses template method pattern with _before_get hook and
    validates the result through the output Pydantic model.

    Миксин репозитория для чтения (GET) одной сущности.

    Использует паттерн Template Method с хуком _before_get
    и валидирует результат через выходную Pydantic-модель.
    """

    async def _before_get(self):
        """Hook called before reading an entity. Override for custom logic.

        Хук, вызываемый перед чтением сущности. Переопределите для своей логики.
        """
        pass

    @abstractmethod
    async def _get(
        self, get_schema: AbstractGetPydanticModel
    ) -> AbstractInternalModel | None:
        """Perform the actual retrieval of an entity.

        Args:
            get_schema: Validated Pydantic model with query parameters.

        Returns:
            The retrieved entity.

        Выполняет фактическое получение сущности.

        Args:
            get_schema: Валидированная Pydantic-модель с параметрами запроса.

        Returns:
            Полученная сущность.
        """
        pass

    async def get(
        self, get_schema: AbstractGetPydanticModel
    ) -> AbstractDefaultPydanticModel:
        """Retrieve an entity and return validated result.

        Args:
            get_schema: Validated Pydantic model with query parameters.

        Returns:
            Validated Pydantic model of the retrieved entity.

        Получает сущность и возвращает валидированный результат.

        Args:
            get_schema: Валидированная Pydantic-модель с параметрами запроса.

        Returns:
            Валидированная Pydantic-модель полученной сущности.
        """
        await self._before_get()
        return self._output_pyd_model.model_validate(
            await self._get(get_schema=get_schema)
        )


AbstractPatchPydanticModel = TypeVar(
    "AbstractPatchPydanticModel", bound=AbstractUpdateBaseModel
)


class AbstractAsyncRepoUpdate(
    Generic[
        AbstractDefaultPydanticModel,
        AbstractPatchPydanticModel,
        AbstractInternalModel,
    ],
    GenericAsyncRepo[AbstractDefaultPydanticModel],
    ABC,
):
    """Mixin repository for updating (PATCH) an entity.

    Uses template method pattern with _before_patch hook and
    validates the result through the output Pydantic model.

    Миксин репозитория для обновления (PATCH) сущности.

    Использует паттерн Template Method с хуком _before_patch
    и валидирует результат через выходную Pydantic-модель.
    """

    async def _before_patch(self):
        """Hook called before updating an entity. Override for custom logic.

        Хук, вызываемый перед обновлением сущности. Переопределите для своей логики.
        """
        pass

    @abstractmethod
    async def _patch(
        self, patch_schema: AbstractPatchPydanticModel
    ) -> AbstractInternalModel:
        """Perform the actual update of an entity.

        Args:
            patch_schema: Validated Pydantic model with update data.

        Returns:
            The updated entity.

        Выполняет фактическое обновление сущности.

        Args:
            patch_schema: Валидированная Pydantic-модель с данными обновления.

        Returns:
            Обновлённая сущность.
        """
        pass

    async def patch(
        self, patch_schema: AbstractPatchPydanticModel
    ) -> AbstractDefaultPydanticModel:
        """Update an entity and return validated result.

        Args:
            patch_schema: Validated Pydantic model with update data.

        Returns:
            Validated Pydantic model of the updated entity.

        Обновляет сущность и возвращает валидированный результат.

        Args:
            patch_schema: Валидированная Pydantic-модель с данными обновления.

        Returns:
            Валидированная Pydantic-модель обновлённой сущности.
        """
        await self._before_patch()
        return self._output_pyd_model.model_validate(
            await self._patch(patch_schema=patch_schema)
        )


AbstractDeletePydanticModel = TypeVar(
    "AbstractDeletePydanticModel", bound=AbstractDeleteBaseModel
)


class AbstractAsyncRepoDelete(
    Generic[
        AbstractDefaultPydanticModel,
        AbstractDeletePydanticModel,
        AbstractInternalModel,
    ],
    GenericAsyncRepo[AbstractDefaultPydanticModel],
    ABC,
):
    """Mixin repository for deleting an entity.

    Uses template method pattern with _before_delete hook and
    validates the result through the output Pydantic model.

    Миксин репозитория для удаления сущности.

    Использует паттерн Template Method с хуком _before_delete
    и валидирует результат через выходную Pydantic-модель.
    """

    async def _before_delete(self):
        """Hook called before deleting an entity. Override for custom logic.

        Хук, вызываемый перед удалением сущности. Переопределите для своей логики.
        """
        pass

    @abstractmethod
    async def _delete(
        self, delete_schema: AbstractDeletePydanticModel
    ) -> AbstractInternalModel:
        """Perform the actual deletion of an entity.

        Args:
            delete_schema: Validated Pydantic model with deletion parameters.

        Returns:
            The deleted entity.

        Выполняет фактическое удаление сущности.

        Args:
            delete_schema: Валидированная Pydantic-модель с параметрами удаления.

        Returns:
            Удалённая сущность.
        """
        pass

    async def delete(
        self, delete_schema: AbstractDeletePydanticModel
    ) -> AbstractDefaultPydanticModel:
        """Delete an entity and return validated result.

        Args:
            delete_schema: Validated Pydantic model with deletion parameters.

        Returns:
            Validated Pydantic model of the deleted entity.

        Удаляет сущность и возвращает валидированный результат.

        Args:
            delete_schema: Валидированная Pydantic-модель с параметрами удаления.

        Returns:
            Валидированная Pydantic-модель удалённой сущности.
        """
        await self._before_delete()
        return self._output_pyd_model.model_validate(
            await self._delete(delete_schema=delete_schema)
        )


AbstractGetPagginatedPydanticModel = TypeVar(
    "AbstractGetPagginatedPydanticModel", bound=AbstractDefaultReadPagginationBaseModel
)
AbstractDefaultPagginatedPydanticModel = TypeVar(
    "AbstractDefaultPagginatedPydanticModel", bound=AbstractDefaultPagginationBaseModel
)


class AbstractAsyncRepoReadPaginated(
    Generic[
        AbstractID,
        AbstractGetPagginatedPydanticModel,
        AbstractDefaultPagginatedPydanticModel,
        AbstractInternalModel,
    ],
    ABC,
):
    """Mixin repository for reading (GET) multiple entities with pagination.

    Provides paginated retrieval with count calculation and
    automatic pagination metadata construction.

    Миксин репозитория для постраничного чтения (GET) нескольких сущностей.

    Предоставляет постраничное получение с подсчётом количества
    и автоматическим формированием метаданных пагинации.
    """

    @property
    @abstractmethod
    def _pagginated_output_pyd_model(
        self,
    ) -> type[AbstractDefaultPagginatedPydanticModel]:
        """Return the Pydantic model class for paginated output validation.

        Возвращает класс Pydantic-модели для валидации постраничного вывода.
        """
        pass

    async def _before_get_many(self):
        """Hook called before reading multiple entities. Override for custom logic.

        Хук, вызываемый перед чтением нескольких сущностей.
        Переопределите для своей логики.
        """
        pass

    @abstractmethod
    async def _get_many(
        self, get_schema: AbstractGetPagginatedPydanticModel
    ) -> list[AbstractInternalModel]:
        """Perform the actual retrieval of multiple entities.

        Args:
            get_schema: Validated Pydantic model with pagination parameters.

        Returns:
            List of retrieved entities.

        Выполняет фактическое получение нескольких сущностей.

        Args:
            get_schema: Валидированная Pydantic-модель с параметрами пагинации.

        Returns:
            Список полученных сущностей.
        """
        pass

    @abstractmethod
    async def _get_count(self, get_schema: AbstractGetPagginatedPydanticModel) -> int:
        """Get total count of entities matching the query.

        Args:
            get_schema: Validated Pydantic model with query parameters.

        Returns:
            Total number of matching entities.

        Возвращает общее количество сущностей, соответствующих запросу.

        Args:
            get_schema: Валидированная Pydantic-модель с параметрами запроса.

        Returns:
            Общее количество совпадающих сущностей.
        """
        pass

    async def _get_prepaired_dict(
        self, get_schema: AbstractGetPagginatedPydanticModel
    ) -> dict[str, int | list[AbstractInternalModel] | AbstractID]:
        """Build a dictionary with pagination data.

        Args:
            get_schema: Validated Pydantic model with pagination parameters.

        Returns:
            Dictionary containing count_pages, items, and page_size.

        Формирует словарь с данными пагинации.

        Args:
            get_schema: Валидированная Pydantic-модель с параметрами пагинации.

        Returns:
            Словарь, содержащий count_pages, items и page_size.
        """
        count = await self._get_count(get_schema)
        items = await self._get_many(get_schema)
        return {
            "count_pages": int(count / get_schema.page_size + 0.5),
            "items": items,
            "page_size": get_schema.page_size,
        }

    async def get_many(
        self, get_schema: AbstractGetPagginatedPydanticModel
    ) -> AbstractDefaultPagginatedPydanticModel:
        """Retrieve paginated entities and return validated result.

        Args:
            get_schema: Validated Pydantic model with pagination parameters.

        Returns:
            Validated Pydantic model with paginated results.

        Получает сущности с пагинацией и возвращает валидированный результат.

        Args:
            get_schema: Валидированная Pydantic-модель с параметрами пагинации.

        Returns:
            Валидированная Pydantic-модель с постраничными результатами.
        """
        await self._before_get_many()
        data = await self._get_prepaired_dict(get_schema)
        return self._pagginated_output_pyd_model.model_validate(data)


# --- Комбинации Репозиториев ---


class AbstractAsyncCRRepo(
    Generic[
        AbstractDefaultPydanticModel,
        AbstractPostPydanticModel,
        AbstractGetPydanticModel,
        AbstractInternalModel,
    ],
    AbstractAsyncRepoCreate[
        AbstractPostPydanticModel, AbstractDefaultPydanticModel, AbstractInternalModel
    ],
    AbstractAsyncRepoRead[
        AbstractDefaultPydanticModel, AbstractGetPydanticModel, AbstractInternalModel
    ],
    ABC,
):
    """Combination repository supporting Create and Read operations.

    Комбинированный репозиторий с поддержкой операций создания и чтения.
    """

    pass


class AbstractAsyncCRURepo(
    Generic[
        AbstractDefaultPydanticModel,
        AbstractPostPydanticModel,
        AbstractGetPydanticModel,
        AbstractPatchPydanticModel,
        AbstractInternalModel,
    ],
    AbstractAsyncRepoCreate[
        AbstractPostPydanticModel, AbstractDefaultPydanticModel, AbstractInternalModel
    ],
    AbstractAsyncRepoRead[
        AbstractDefaultPydanticModel, AbstractGetPydanticModel, AbstractInternalModel
    ],
    AbstractAsyncRepoUpdate[
        AbstractDefaultPydanticModel, AbstractPatchPydanticModel, AbstractInternalModel
    ],
    ABC,
):
    """Combination repository supporting Create, Read, and Update operations.

    Комбинированный репозиторий с поддержкой создания, чтения и обновления.
    """

    pass


class AbstractAsyncCRDRepo(
    Generic[
        AbstractDefaultPydanticModel,
        AbstractPostPydanticModel,
        AbstractGetPydanticModel,
        AbstractDeletePydanticModel,
        AbstractInternalModel,
    ],
    AbstractAsyncRepoCreate[
        AbstractPostPydanticModel, AbstractDefaultPydanticModel, AbstractInternalModel
    ],
    AbstractAsyncRepoRead[
        AbstractDefaultPydanticModel, AbstractGetPydanticModel, AbstractInternalModel
    ],
    AbstractAsyncRepoDelete[
        AbstractDefaultPydanticModel, AbstractDeletePydanticModel, AbstractInternalModel
    ],
    ABC,
):
    """Combination repository supporting Create, Read, and Delete operations.

    Комбинированный репозиторий с поддержкой создания, чтения и удаления.
    """

    pass


class AbstractAsyncRUDRepo(
    Generic[
        AbstractDefaultPydanticModel,
        AbstractGetPydanticModel,
        AbstractPatchPydanticModel,
        AbstractDeletePydanticModel,
        AbstractInternalModel,
    ],
    AbstractAsyncRepoRead[
        AbstractDefaultPydanticModel, AbstractGetPydanticModel, AbstractInternalModel
    ],
    AbstractAsyncRepoUpdate[
        AbstractDefaultPydanticModel, AbstractPatchPydanticModel, AbstractInternalModel
    ],
    AbstractAsyncRepoDelete[
        AbstractDefaultPydanticModel, AbstractDeletePydanticModel, AbstractInternalModel
    ],
    ABC,
):
    """Combination repository supporting Read, Update, and Delete operations.

    Комбинированный репозиторий с поддержкой чтения, обновления и удаления.
    """

    pass


class AbstractAsyncCRUDRepo(
    Generic[
        AbstractDefaultPydanticModel,
        AbstractPostPydanticModel,
        AbstractGetPydanticModel,
        AbstractPatchPydanticModel,
        AbstractDeletePydanticModel,
        AbstractInternalModel,
    ],
    AbstractAsyncRepoCreate[
        AbstractPostPydanticModel, AbstractDefaultPydanticModel, AbstractInternalModel
    ],
    AbstractAsyncRepoRead[
        AbstractDefaultPydanticModel, AbstractGetPydanticModel, AbstractInternalModel
    ],
    AbstractAsyncRepoUpdate[
        AbstractDefaultPydanticModel, AbstractPatchPydanticModel, AbstractInternalModel
    ],
    AbstractAsyncRepoDelete[
        AbstractDefaultPydanticModel, AbstractDeletePydanticModel, AbstractInternalModel
    ],
    ABC,
):
    """Combination repository supporting full CRUD operations.

    Комбинированный репозиторий с полным набором CRUD-операций.
    """

    pass


class AbstractAsyncCRUPRepo(
    Generic[
        AbstractID,
        AbstractDefaultPydanticModel,
        AbstractPostPydanticModel,
        AbstractGetPydanticModel,
        AbstractPatchPydanticModel,
        AbstractGetPagginatedPydanticModel,
        AbstractDefaultPagginatedPydanticModel,
        AbstractInternalModel,
    ],
    AbstractAsyncRepoCreate[
        AbstractPostPydanticModel, AbstractDefaultPydanticModel, AbstractInternalModel
    ],
    AbstractAsyncRepoRead[
        AbstractDefaultPydanticModel, AbstractGetPydanticModel, AbstractInternalModel
    ],
    AbstractAsyncRepoUpdate[
        AbstractDefaultPydanticModel, AbstractPatchPydanticModel, AbstractInternalModel
    ],
    AbstractAsyncRepoReadPaginated[
        AbstractID,
        AbstractGetPagginatedPydanticModel,
        AbstractDefaultPagginatedPydanticModel,
        AbstractInternalModel,
    ],
    ABC,
):
    """Combination repository supporting Create, Read,
    Update, and Paginated Read operations.

    Комбинированный репозиторий с поддержкой создания, чтения,
    обновления и постраничного чтения.
    """

    pass


class AbstractAsyncCRDPRepo(
    Generic[
        AbstractID,
        AbstractDefaultPydanticModel,
        AbstractPostPydanticModel,
        AbstractGetPydanticModel,
        AbstractDeletePydanticModel,
        AbstractGetPagginatedPydanticModel,
        AbstractDefaultPagginatedPydanticModel,
        AbstractInternalModel,
    ],
    AbstractAsyncRepoCreate[
        AbstractPostPydanticModel, AbstractDefaultPydanticModel, AbstractInternalModel
    ],
    AbstractAsyncRepoRead[
        AbstractDefaultPydanticModel, AbstractGetPydanticModel, AbstractInternalModel
    ],
    AbstractAsyncRepoDelete[
        AbstractDefaultPydanticModel, AbstractDeletePydanticModel, AbstractInternalModel
    ],
    AbstractAsyncRepoReadPaginated[
        AbstractID,
        AbstractGetPagginatedPydanticModel,
        AbstractDefaultPagginatedPydanticModel,
        AbstractInternalModel,
    ],
    ABC,
):
    """Combination repository supporting Create, Read,
    Delete, and Paginated Read operations.

    Комбинированный репозиторий с поддержкой создания, чтения,
    удаления и постраничного чтения.
    """

    pass


class AbstractAsyncRUDPRepo(
    Generic[
        AbstractID,
        AbstractDefaultPydanticModel,
        AbstractGetPydanticModel,
        AbstractPatchPydanticModel,
        AbstractDeletePydanticModel,
        AbstractGetPagginatedPydanticModel,
        AbstractDefaultPagginatedPydanticModel,
        AbstractInternalModel,
    ],
    AbstractAsyncRepoRead[
        AbstractDefaultPydanticModel, AbstractGetPydanticModel, AbstractInternalModel
    ],
    AbstractAsyncRepoUpdate[
        AbstractDefaultPydanticModel, AbstractPatchPydanticModel, AbstractInternalModel
    ],
    AbstractAsyncRepoDelete[
        AbstractDefaultPydanticModel, AbstractDeletePydanticModel, AbstractInternalModel
    ],
    AbstractAsyncRepoReadPaginated[
        AbstractID,
        AbstractGetPagginatedPydanticModel,
        AbstractDefaultPagginatedPydanticModel,
        AbstractInternalModel,
    ],
    ABC,
):
    """Combination repository supporting Read, Update,
    Delete, and Paginated Read operations.

    Комбинированный репозиторий с поддержкой чтения,
    обновления, удаления и постраничного чтения.
    """

    pass


class AbstractAsyncCRUDPRepo(
    Generic[
        AbstractID,
        AbstractDefaultPydanticModel,
        AbstractPostPydanticModel,
        AbstractGetPydanticModel,
        AbstractPatchPydanticModel,
        AbstractDeletePydanticModel,
        AbstractGetPagginatedPydanticModel,
        AbstractDefaultPagginatedPydanticModel,
        AbstractInternalModel,
    ],
    AbstractAsyncRepoCreate[
        AbstractPostPydanticModel, AbstractDefaultPydanticModel, AbstractInternalModel
    ],
    AbstractAsyncRepoRead[
        AbstractDefaultPydanticModel, AbstractGetPydanticModel, AbstractInternalModel
    ],
    AbstractAsyncRepoUpdate[
        AbstractDefaultPydanticModel, AbstractPatchPydanticModel, AbstractInternalModel
    ],
    AbstractAsyncRepoDelete[
        AbstractDefaultPydanticModel, AbstractDeletePydanticModel, AbstractInternalModel
    ],
    AbstractAsyncRepoReadPaginated[
        AbstractID,
        AbstractGetPagginatedPydanticModel,
        AbstractDefaultPagginatedPydanticModel,
        AbstractInternalModel,
    ],
    ABC,
):
    """Combination repository supporting full CRUD plus Paginated Read operations.

    Комбинированный репозиторий с полным CRUD и постраничным чтением.
    """

    pass

"""Repository layer for dialog chats and messages database operations.

Слой репозитория для операций с базой данных диалогов и сообщений.
"""

from uuid import UUID

from sqlalchemy import Select, select, union_all

from shared.basic_repository import (
    AbstractUUIDSQLAlchemyCRDP,
    AbstractUUIDSQLAlchemyCRP,
)
from shared.basic_schemas import UUIDGetPagginationBaseModel

from .models import DialogChat, DialogMessage
from .schemas import (
    DefaultDialogChat,
    DefaultDialogMessage,
    DeleteDialogChat,
    GetDialogChat,
    GetDialogMessage,
    PagginationDialogChats,
    PagginationDialogMessage,
    PostDialogChat,
    PostDialogMessage,
)


class DialogChatRepo(
    AbstractUUIDSQLAlchemyCRDP[
        DialogChat,
        DefaultDialogChat,
        PostDialogChat,
        GetDialogChat,
        DeleteDialogChat,
        PagginationDialogChats,
    ]
):
    """Repository for dialog chat database operations.

    Репозиторий для операций с базой данных диалогов.
    """

    async def _post(self, post_schema: PostDialogChat) -> DialogChat:
        """Create a DialogChat from PostDialogChat.

        PostDialogChat contains {name, user}, where `user` is the OTHER
        participant's id. DialogChat has two columns: user0 (caller)
        and user1 (counterparty). The base AbstractDefaultSQLAlchemyCreate.
        _post would forward kwargs verbatim into DialogChat(...), which
        has no `user` column, hence TypeError.

        Здесь раскладываем schema.user в user1 и подставляем залогиненного
        пользователя в user0.

        Args:
            post_schema: Validated creation schema.

        Returns:
            The created DialogChat instance with refreshed state.
        """
        new = DialogChat(
            name=post_schema.name,
            user0=self._user.id,
            user1=post_schema.user,
        )
        self._session.add(new)
        await self._session.flush()
        await self._session.commit()
        return new

    @property
    def _model(self) -> type[DialogChat]:
        """Return the SQLAlchemy model class for DialogChat.

        Возвращает класс SQLAlchemy-модели для DialogChat.
        """
        return DialogChat

    @property
    def _output_pyd_model(self) -> type[DefaultDialogChat]:
        """Return the Pydantic model class for output validation.

        Возвращает класс Pydantic-модели для валидации выходных данных.
        """
        return DefaultDialogChat

    @property
    def _pagginated_output_pyd_model(self) -> type[PagginationDialogChats]:
        """Return the Pydantic model class for paginated output validation.

        Возвращает класс Pydantic-модели для валидации постраничного вывода.
        """
        return PagginationDialogChats

    async def _get_one_obj_using_id(self, id: UUID) -> DialogChat:
        """Retrieve a single DialogChat by its ID.

        Получает один DialogChat по его ID.

        Args:
            id: The primary key value. Значение первичного ключа.

        Returns:
            The DialogChat instance. Экземпляр DialogChat.
        """
        obj = await self._session.get(DialogChat, id)
        if obj is None:
            raise ValueError(f"DialogChat with id={id} not found")
        return obj

    async def _based_select(self) -> Select:
        """Build and return a base SELECT statement for DialogChat.

        Формирует и возвращает базовый SELECT-запрос для DialogChat.

        Returns:
            A SQLAlchemy Select object with the base query.
            Объект SQLAlchemy Select с базовым запросом.
        """
        return select(DialogChat)

    def _get_many_stmt(self, get_schema: PagginationDialogChats) -> Select:
        """Build SELECT statement for retrieving chats for current user.

        Строит SELECT-запрос для получения чатов текущего пользователя.

        Args:
            get_schema: Pagination schema with query parameters.
                Схема пагинации с параметрами запроса.

        Returns:
            SQLAlchemy Select statement combining user0 and user1 chats.
                SQLAlchemy Select-запрос, объединяющий чаты user0 и user1.
        """
        user0_select = select(DialogChat).where(DialogChat.user0 == self._user.id)
        user1_select = select(DialogChat).where(DialogChat.user1 == self._user.id)
        return union_all(user0_select, user1_select)


class DialogMessageRepo(
    AbstractUUIDSQLAlchemyCRP[
        DialogMessage,
        DefaultDialogMessage,
        PostDialogMessage,
        GetDialogMessage,
        PagginationDialogMessage,
    ]
):
    """Repository for dialog message database operations.

    Репозиторий для операций с базой данных сообщений диалога.
    """

    @property
    def _model(self) -> type[DialogMessage]:
        """Return the SQLAlchemy model class for DialogMessage.

        Возвращает класс SQLAlchemy-модели для DialogMessage.
        """
        return DialogMessage

    @property
    def _output_pyd_model(self) -> type[DefaultDialogMessage]:
        """Return the Pydantic model class for output validation.

        Возвращает класс Pydantic-модели для валидации выходных данных.
        """
        return DefaultDialogMessage

    @property
    def _pagginated_output_pyd_model(self) -> type[PagginationDialogMessage]:
        """Return the Pydantic model class for paginated output validation.

        Возвращает класс Pydantic-модели для валидации постраничного вывода.
        """
        return PagginationDialogMessage

    async def _get_one_obj_using_id(self, id: UUID) -> DialogMessage:
        """Retrieve a single DialogMessage by its ID.

        Получает один DialogMessage по его ID.

        Args:
            id: The primary key value. Значение первичного ключа.

        Returns:
            The DialogMessage instance. Экземпляр DialogMessage.
        """
        obj = await self._session.get(DialogMessage, id)
        if obj is None:
            raise ValueError(f"DialogMessage with id={id} not found")
        return obj

    async def _based_select(self) -> Select:
        """Build and return a base SELECT statement for DialogMessage.

        Формирует и возвращает базовый SELECT-запрос для DialogMessage.

        Returns:
            A SQLAlchemy Select object with the base query.
            Объект SQLAlchemy Select с базовым запросом.
        """
        return select(DialogMessage)

    def _get_many_stmt(self, get_schema: UUIDGetPagginationBaseModel) -> Select:
        """Build SELECT statement for retrieving messages.

        Строит SELECT-запрос для получения сообщений.

        Args:
            get_schema: Pagination schema with query parameters.
                Схема пагинации с параметрами запроса.

        Returns:
            A SQLAlchemy Select object with the base query.
            Объект SQLAlchemy Select с базовым запросом.
        """
        return select(DialogMessage).where(DialogMessage.chat_id == get_schema.id)  # type: ignore[return-value]

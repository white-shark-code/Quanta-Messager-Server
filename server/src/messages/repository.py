"""Repository layer for dialog chats and messages database operations.

Слой репозитория для операций с базой данных диалогов и сообщений.
"""

from uuid import UUID

from sqlalchemy import Select, func, or_, select, union_all

from authentication.models import UserGroup
from shared.basic_repository import (
    AbstractUUIDSQLAlchemyCRDP,
    AbstractUUIDSQLAlchemyCRP,
)
from shared.basic_schemas import UUIDGetPagginationBaseModel

from .models import DialogChat, DialogMessage, GroupChat
from .schemas import (
    DefaultDialogChat,
    DefaultDialogMessage,
    DefaultGroupChat,
    DeleteDialogChat,
    DeleteGroupChat,
    GetDialogChat,
    GetDialogMessage,
    GetGroupChat,
    PagginationDialogChats,
    PagginationDialogMessage,
    PagginationGroupChats,
    PostDialogChat,
    PostDialogMessage,
    PostGroupChat,
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
        """Build cursor-paginated SELECT of all chats where the user participates.

        Uses `OR` to filter by `user0` or `user1`, ordered by `id` for cursor.

        Args:
            get_schema: Pagination schema with `last_id` and `page_size`.

        Returns:
            SQLAlchemy Select statement ready for execution.
        """
        stmt: Select = select(DialogChat).where(
            or_(
                DialogChat.user0 == self._user.id,
                DialogChat.user1 == self._user.id,
            )
        )
        if get_schema.last_id is not None:
            stmt = stmt.where(DialogChat.id > get_schema.last_id)
        return stmt.order_by(DialogChat.id).limit(get_schema.page_size)

    async def _get_count(self, get_schema: PagginationDialogChats) -> int:
        """Count total chats matching cursor predicate (excluding LIMIT).

        Подсчитывает общее число чатов по фильтру курсора (без учёта LIMIT).
        """
        stmt = select(func.count()).select_from(DialogChat).where(
            or_(
                DialogChat.user0 == self._user.id,
                DialogChat.user1 == self._user.id,
            )
        )
        if get_schema.last_id is not None:
            stmt = stmt.where(DialogChat.id > get_schema.last_id)
        count_result = await self._session.execute(stmt)
        return int(count_result.scalar_one())


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
            SQLAlchemy Select statement with the base query.
                SQLAlchemy Select-запрос с базовым запросом.
        """
        return select(DialogMessage).where(DialogMessage.chat_id == get_schema.id)  # type: ignore[return-value]


class GroupChatRepo(
    AbstractUUIDSQLAlchemyCRDP[
        GroupChat,
        DefaultGroupChat,
        PostGroupChat,
        GetGroupChat,
        DeleteGroupChat,
        PagginationGroupChats,
    ]
):
    """Repository for group chat database operations.

    Репозиторий для операций с базой данных групповых чатов.
    """

    async def _post(self, post_schema: PostGroupChat) -> GroupChat:
        """Create a GroupChat from PostGroupChat.

        Flushes only; the facade handles the post-create hook
        (membership insert) and commits.

        Args:
            post_schema: Validated creation schema with name and public_key.

        Returns:
            The created GroupChat instance.
        """
        new = GroupChat(
            name=post_schema.name,
            public_key=post_schema.public_key,
        )
        self._session.add(new)
        await self._session.flush()
        await self._session.refresh(new)
        return new

    @property
    def _model(self) -> type[GroupChat]:
        """Return the SQLAlchemy model class for GroupChat.

        Возвращает класс SQLAlchemy-модели для GroupChat.
        """
        return GroupChat

    @property
    def _output_pyd_model(self) -> type[DefaultGroupChat]:
        """Return the Pydantic model class for output validation.

        Возвращает класс Pydantic-модели для валидации выходных данных.
        """
        return DefaultGroupChat

    @property
    def _pagginated_output_pyd_model(self) -> type[PagginationGroupChats]:
        """Return the Pydantic model class for paginated output validation.

        Возвращает класс Pydantic-модели для валидации постраничного вывода.
        """
        return PagginationGroupChats

    async def _get_one_obj_using_id(self, id: UUID) -> GroupChat:
        """Retrieve a single GroupChat by its ID.

        Получает один GroupChat по его ID.

        Args:
            id: The primary key value.

        Returns:
            The GroupChat instance.

        Raises:
            ValueError: If the chat is not found.
        """
        obj = await self._session.get(GroupChat, id)
        if obj is None:
            raise ValueError(f"GroupChat with id={id} not found")
        return obj

    async def _based_select(self) -> Select:
        """Build and return a base SELECT statement for GroupChat.

        Формирует базовый SELECT-запрос для GroupChat.
        """
        return select(GroupChat)

    def _get_many_stmt(self, get_schema: PagginationGroupChats) -> Select:
        """Build cursor-paginated SELECT of group chats where the user is a member.

        Joins `user_groups` to filter only chats where the current user
        participates. Cursor pagination on `id`.

        Строит cursor-пагинированный SELECT групповых чатов, в которых
        пользователь — участник (через JOIN user_groups).

        Args:
            get_schema: Pagination schema with `last_id` and `page_size`.

        Returns:
            SQLAlchemy Select statement ready for execution.
        """
        stmt: Select = (
            select(GroupChat)
            .join(UserGroup, UserGroup.group_chat_id == GroupChat.id)
            .where(UserGroup.user_id == self._user.id)
        )
        if get_schema.last_id is not None:
            stmt = stmt.where(GroupChat.id > get_schema.last_id)
        return stmt.order_by(GroupChat.id).limit(get_schema.page_size)

    async def _get_count(self, get_schema: PagginationGroupChats) -> int:
        """Count total group chats matching cursor predicate (excluding LIMIT).

        Подсчитывает общее число групповых чатов по фильтру курсора.
        """
        stmt = select(func.count()).select_from(GroupChat).join(
            UserGroup, UserGroup.group_chat_id == GroupChat.id
        ).where(UserGroup.user_id == self._user.id)
        if get_schema.last_id is not None:
            stmt = stmt.where(GroupChat.id > get_schema.last_id)
        count_result = await self._session.execute(stmt)
        return int(count_result.scalar_one())

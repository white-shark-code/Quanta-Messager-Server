"""Repository layer for dialog chats and messages database operations.

Слой репозитория для операций с базой данных диалогов и сообщений.
"""

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
        PagginationDialogChats
    ]
):
    """Repository for dialog chat database operations.

    Репозиторий для операций с базой данных диалогов.
    """

    def _get_many_stmt(
        self,
        get_schema: PagginationDialogChats
    ) -> Select:
        """Build SELECT statement for retrieving chats for current user.

        Строит SELECT-запрос для получения чатов текущего пользователя.

        Args:
            get_schema: Pagination schema with query parameters.
                Схема пагинации с параметрами запроса.

        Returns:
            SQLAlchemy Select statement combining user0 and user1 chats.
                SQLAlchemy Select-запрос, объединяющий чаты user0 и user1.
        """
        user0_select = select(DialogChat).where(DialogChat.user0 == self.user.id)
        user1_select = select(DialogChat).where(DialogChat.user1 == self.user.id)
        return union_all(user0_select, user1_select)


class DialogMessageRepo(
    AbstractUUIDSQLAlchemyCRP[
        DialogMessage,
        DefaultDialogMessage,
        PostDialogMessage,
        GetDialogMessage,
        PagginationDialogMessage
    ]
):
    """Repository for dialog message database operations.

    Репозиторий для операций с базой данных сообщений диалога.
    """

    async def _get_many_stmt(
        self,
        get_schema: UUIDGetPagginationBaseModel
    ):
        """Build SELECT statement for retrieving messages.

        Строит SELECT-запрос для получения сообщений.

        Args:
            get_schema: Pagination schema with query parameters.
                Схема пагинации с параметрами запроса.
        """
        pass

    async def _get_prepaired_dict():
        """Get prepared dictionary for message operations.

        Получить подготовленный словарь для операций с сообщениями.
        """

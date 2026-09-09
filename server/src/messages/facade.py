"""Facade layer for dialog operations with business logic hooks.

Фасад для операций с диалогами с хуками бизнес-логики.
"""

from sqlalchemy.exc import NoResultFound

from authentication.models import User, UserGroup
from authentication.schemas import Roles
from shared.abstract_facade import AbstractFacadeCRDP
from shared.basic_schemas import UUIDGetPagginationBaseModel
from shared.exceptions import (
    ChatAccessDeniedException,
    ChatNotFoundException,
    UserNotFoundException,
)

from .models import DialogChat, GroupChat
from .repository import DialogChatRepo, GroupChatRepo
from .schemas import (
    DefaultDialogChat,
    DefaultGroupChat,
    DeleteDialogChat,
    DeleteGroupChat,
    GetDialogChat,
    GetGroupChat,
    PagginationDialogChats,
    PagginationGroupChats,
    PostDialogChat,
    PostGroupChat,
)


class DialogFacade(
    AbstractFacadeCRDP[
        DialogChatRepo,
        DefaultDialogChat,
        PostDialogChat,
        GetDialogChat,
        DeleteDialogChat,
        UUIDGetPagginationBaseModel,
        PagginationDialogChats,
    ]
):
    """Facade for dialog operations using AbstractFacadeCRDP structure.

    Фасад для работы с диалогами.
    Использует структуру AbstractFacadeCRDP, бизнес-логика в хуках.
    Исключения пробрасываются наверх для обработки глобальными обработчиками.
    """

    async def _before_create(self, schema: PostDialogChat) -> PostDialogChat:
        """Validate that the target user exists before creating a chat.

        Проверяет существование целевого пользователя перед созданием чата.

        Args:
            schema: The chat creation schema containing the target user ID.

        Returns:
            The validated creation schema.

        Raises:
            UserNotFoundException: If the target user does not exist.
        """
        try:
            await self._session.get_one(entity=User, ident=schema.user)
        except NoResultFound:
            raise UserNotFoundException(user_id=str(schema.user))
        return schema

    async def _after_read(self, result: DefaultDialogChat) -> DefaultDialogChat:
        """Verify the current user has access to the retrieved chat.

        Проверяет, что текущий пользователь имеет доступ к полученному чату.

        Args:
            result: The retrieved dialog chat data.

        Returns:
            The validated chat data if access is granted.

        Raises:
            ChatAccessDeniedException: If the user is not a participant in the chat.
        """
        if self._user.id not in [result.user0, result.user1]:
            raise ChatAccessDeniedException(
                chat_id=str(result.id), user_id=str(self._user.id)
            )
        return result

    async def _before_delete(self, schema: DeleteDialogChat) -> DeleteDialogChat:
        """Verify chat exists and user has permission before deletion.

        Проверяет существование чата и права пользователя перед удалением.

        Args:
            schema: The deletion schema containing the chat ID.

        Returns:
            The validated deletion schema.

        Raises:
            ChatNotFoundException: If the chat does not exist.
            ChatAccessDeniedException: If the user is not a participant.
        """
        try:
            dchat = await self._session.get_one(entity=DialogChat, ident=schema.id)
            if self._user.id not in [dchat.user0, dchat.user1]:
                raise ChatAccessDeniedException(
                    chat_id=str(schema.id), user_id=str(self._user.id)
                )
        except NoResultFound:
            raise ChatNotFoundException(
                chat_id=str(schema.id), user_id=str(self._user.id)
            )
        return schema

    async def get_all_chats(
        self, paginate: UUIDGetPagginationBaseModel
    ) -> PagginationDialogChats:
        """List all dialog chats where the current user participates.

        Returns a cursor-paginated page of chats. Access is already
        enforced at the SQL level by the repository's union over
        user0/user1, so no per-item access check is required.

        Возвращает cursor-пагинированную страницу диалогов, где текущий
        пользователь — участник. Доступ уже ограничен на уровне SQL.

        Args:
            paginate: Cursor pagination schema (`last_id` and `page_size`).

        Returns:
            Paginated dialog chats response.
        """
        return await self.read_paginated(paginate)


class GroupChatFacade(
    AbstractFacadeCRDP[
        GroupChatRepo,
        DefaultGroupChat,
        PostGroupChat,
        GetGroupChat,
        DeleteGroupChat,
        UUIDGetPagginationBaseModel,
        PagginationGroupChats,
    ]
):
    """Facade for group chat operations.

    Фасад для операций с групповыми чатами.
    """

    async def _before_create(self, schema: PostGroupChat) -> PostGroupChat:
        """No pre-create validation needed; the schema carries its own key.

        Перед созданием дополнительная валидация не требуется: публичный
        ключ группы передаётся в схеме.
        """
        return schema

    async def _after_create(self, result: DefaultGroupChat) -> None:
        """Add the creator as ADMIN member of the new group chat and commit.

        Добавляет создателя в участники нового чата с ролью ADMIN
        и коммитит транзакцию.

        Args:
            result: The created group chat.
        """
        self._session.add(
            UserGroup(
                user_id=self._user.id,
                group_chat_id=result.id,
                role=Roles.ADMIN,
            )
        )
        await self._session.flush()
        await self._session.commit()

    async def _after_read(self, result: DefaultGroupChat) -> DefaultGroupChat:
        """Verify the current user is a member of the retrieved group chat.

        Проверяет, что текущий пользователь — участник группового чата.

        Args:
            result: The retrieved group chat.

        Returns:
            The validated group chat.

        Raises:
            ChatAccessDeniedException: If the user is not a member.
        """
        try:
            await self._session.get_one(
                entity=UserGroup,
                ident=(self._user.id, result.id),
            )
        except NoResultFound as e:
            raise ChatAccessDeniedException(
                chat_id=str(result.id), user_id=str(self._user.id)
            ) from e
        return result

    async def _before_delete(self, schema: DeleteGroupChat) -> DeleteGroupChat:
        """Verify chat exists and user has permission before deletion.

        Проверяет существование чата и права пользователя перед удалением.

        Args:
            schema: The deletion schema containing the chat ID.

        Returns:
            The validated deletion schema.

        Raises:
            ChatNotFoundException: If the chat does not exist.
            ChatAccessDeniedException: If the user is not a member.
        """
        try:
            gchat = await self._session.get_one(entity=GroupChat, ident=schema.id)
            await self._session.get_one(
                entity=UserGroup, ident=(self._user.id, gchat.id)
            )
        except NoResultFound:
            raise ChatNotFoundException(
                chat_id=str(schema.id), user_id=str(self._user.id)
            )
        return schema

    async def get_all_chats(
        self, paginate: UUIDGetPagginationBaseModel
    ) -> PagginationGroupChats:
        """List all group chats where the current user is a member.

        Access is enforced at the SQL level via JOIN on `user_groups`.

        Возвращает cursor-пагинированную страницу групповых чатов,
        в которых пользователь — участник.

        Args:
            paginate: Cursor pagination schema (`last_id` and `page_size`).

        Returns:
            Paginated group chats response.
        """
        return await self.read_paginated(paginate)

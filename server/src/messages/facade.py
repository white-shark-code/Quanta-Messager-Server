"""Facade layer for dialog operations with business logic hooks.

Фасад для операций с диалогами с хуками бизнес-логики.
"""
from sqlalchemy.exc import NoResultFound

from authentication.models import User
from shared.abstract_facade import AbstractFacadeCRDP
from shared.basic_schemas import UUIDGetPagginationBaseModel
from shared.exceptions import (
    ChatAccessDeniedException,
    ChatNotFoundException,
    UserNotFoundException,
)

from .models import DialogChat
from .repository import DialogChatRepo
from .schemas import (
    DefaultDialogChat,
    DeleteDialogChat,
    GetDialogChat,
    PagginationDialogChats,
    PostDialogChat,
)


class DialogFacade(
    AbstractFacadeCRDP[
        DialogChatRepo,
        DefaultDialogChat,
        PostDialogChat,
        GetDialogChat,
        DeleteDialogChat,
        UUIDGetPagginationBaseModel,
        PagginationDialogChats
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
                chat_id=str(result.id),
                user_id=str(self._user.id)
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
                    chat_id=str(schema.id),
                    user_id=str(self._user.id)
                )
        except NoResultFound:
            raise ChatNotFoundException(
                chat_id=str(schema.id),
                user_id=str(self._user.id)
            )
        return schema

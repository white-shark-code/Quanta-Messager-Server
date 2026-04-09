from sqlalchemy import select, union_all
from sqlalchemy.exc import NoResultFound

from shared.abstract_facade import AbstractFacadeCRUDP
from shared.basic_schemas import UUIDReadPagginationBaseModel
from shared.exceptions import (
    ChatAccessDeniedException,
    ChatNotFoundException,
    UserNotFoundException,
)

from authentication.models import User
from .models import DialogChat
from .repository import DialogChatRepo
from .schemas import (
    DefaultDialogChat,
    PostDialogChat,
    GetDialogChat,
    PatchDialogChat,
    DeleteDialogChat,
    PagginationDialogChats,
    ListItems,
)


class DialogFacade(
    AbstractFacadeCRUDP[
        DialogChatRepo,
        DefaultDialogChat,
        PostDialogChat,
        GetDialogChat,
        PatchDialogChat,
        DeleteDialogChat,
        UUIDReadPagginationBaseModel,
        PagginationDialogChats
    ]
):
    """
    Фасад для работы с диалогами.
    Использует структуру AbstractFacadeCRUDP, бизнес-логика в хуках.
    Исключения пробрасываются наверх для обработки глобальными обработчиками.
    """

    async def _before_create(self, schema: PostDialogChat) -> PostDialogChat:
        try:
            await self.session.get_one(entity=User, ident=schema.user)
        except NoResultFound:
            raise UserNotFoundException(user_id=str(schema.user))
        return schema

    async def _after_read(self, result: DefaultDialogChat) -> DefaultDialogChat:
        if self.user.id not in [result.user0, result.user1]:
            raise ChatAccessDeniedException(chat_id=str(result.id), user_id=str(self.user.id))
        return result

    async def _before_delete(self, schema: DeleteDialogChat) -> DeleteDialogChat:
        try:
            dchat = await self.session.get_one(entity=DialogChat, ident=schema.id)
            if self.user.id not in [dchat.user0, dchat.user1]:
                raise ChatAccessDeniedException(chat_id=str(schema.id), user_id=str(self.user.id))
        except NoResultFound:
            raise ChatNotFoundException(chat_id=str(schema.id), user_id=str(self.user.id))
        return schema

    async def get_all_chats(self) -> ListItems[DefaultDialogChat]:
        user0_select = select(DialogChat).where(DialogChat.user0 == self.user.id)
        user1_select = select(DialogChat).where(DialogChat.user1 == self.user.id)
        union_select = union_all(user0_select, user1_select)

        val = await self.session.execute(union_select)
        items = [DefaultDialogChat.model_validate(item) for item in val.scalars().all()]
        return ListItems[DefaultDialogChat](items=items)

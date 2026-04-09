from uuid import UUID
from .models import DialogChat
from .schemas import (
    DefaultDialogChat,
    PostDialogChat,
    GetDialogChat,
    DeleteDialogChat,
    PagginationDialogChats
)
from shared.basic_repository import AbstractUUIDSQLAlchemyCRDP


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
    pass

from uuid import UUID
from .models import DialogChat
from .schemas import (
    DefaultDialogChat,
    PostDialogChat,
    GetDialogChat,
    PatchDialogChat,
    DeleteDialogChat,
    PagginationDialogChats
)
from shared.basic_repository import AbstractUUIDSQLAlchemyCRUDP


class DialogChatRepo(
    AbstractUUIDSQLAlchemyCRUDP[
        DialogChat,
        DefaultDialogChat,
        PostDialogChat,
        GetDialogChat,
        PatchDialogChat,
        DeleteDialogChat,
        PagginationDialogChats
    ]
):
    pass

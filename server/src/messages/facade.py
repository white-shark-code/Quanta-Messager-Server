from shared.abstract_facade import AbstractFacadeCRUDP
from shared.basic_schemas import UUIDReadPagginationBaseModel
from .repository import DialogChatRepo
from .schemas import (
    DefaultDialogChat,
    PostDialogChat,
    GetDialogChat,
    PatchDialogChat,
    DeleteDialogChat,
    PagginationDialogChats
)


class DialogFacade(
    AbstractFacadeCRUDP[
        DialogChatRepo,
        PostDialogChat,
        GetDialogChat,
        PatchDialogChat,
        DeleteDialogChat,
        UUIDReadPagginationBaseModel,
        PagginationDialogChats,
        DefaultDialogChat
    ]
):
    """
    Фасад для работы с диалогами.
    Инкапсулирует бизнес-логику и делегирует выполнение репозиторию DialogChatRepo.
    """
    pass



class AppException(Exception):
    """
    Базовое кастомное исключение приложения.
    Содержит разделенную информацию для пользователя, разработчика и администратора.
    """
    def __init__(
        self,
        status_code: int,
        user_message: str,
        dev_message: str,
        admin_message: str,
    ):
        self.status_code = status_code
        self.user_message = user_message
        self.dev_message = dev_message
        self.admin_message = admin_message
        super().__init__(user_message)


# ==================
# Events Exceptions
# ==================

class EventNotFoundException(AppException):
    def __init__(self, event_id: str, user_id: str):
        super().__init__(
            status_code=404,
            user_message="Событие не найдено.",
            dev_message=f"EventInChat with id={event_id} not found in DB.",
            admin_message=f"User {user_id} requested non-existent event {event_id}."
        )


class EventAccessDeniedException(AppException):
    def __init__(self, event_id: str, user_id: str):
        super().__init__(
            status_code=404,  # 404 для пользователя, чтобы не палить чужие ID
            user_message="Событие не найдено.",
            dev_message=(
                f"Access Denied: User {user_id} tried to access event "
                f"{event_id} owned by another user."
            ),
            admin_message=(
                f"User {user_id} attempted to access event "
                f"{event_id} without permission."
            )
        )


# ===================
# Messages Exceptions
# ===================

class UserNotFoundException(AppException):
    def __init__(self, user_id: str):
        super().__init__(
            status_code=404,
            user_message="Пользователь не найден.",
            dev_message=f"User with id={user_id} not found in DB.",
            admin_message=f"Attempt to interact with non-existent user {user_id}."
        )


class ChatNotFoundException(AppException):
    def __init__(self, chat_id: str, user_id: str | None = None):
        user_msg = "Чат не найден."
        dev_msg = f"Chat with id={chat_id} not found in DB."
        admin_msg = f"Chat {chat_id} not found."

        if user_id:
            admin_msg = f"User {user_id} requested non-existent chat {chat_id}."

        super().__init__(
            status_code=404,
            user_message=user_msg,
            dev_message=dev_msg,
            admin_message=admin_msg
        )


class ChatAccessDeniedException(AppException):
    def __init__(self, chat_id: str, user_id: str):
        super().__init__(
            status_code=404,  # 404 для пользователя, чтобы не палить чужие ID
            user_message="Чат не найден.",
            dev_message=(
                f"Access Denied: User {user_id} tried to access chat "
                f"{chat_id} without being a member."
            ),
            admin_message=(
                f"User {user_id} attempted to access chat "
                f"{chat_id} without permission."
            )
        )


class PublicKeyNotSetException(AppException):
    def __init__(self, user_id: str):
        super().__init__(
            status_code=403,  # 403 Forbidden более подходит, чем 405
            user_message="Необходимо добавить публичный ключ.",
            dev_message=f"User {user_id} has no public_key set.",
            admin_message=f"Action blocked for user {user_id}: missing PGP key."
        )


class InvalidSignatureException(AppException):
    def __init__(self, user_id: str, chat_id: str | None = None):
        admin_msg = f"Possible tampering/forgery attempt by user {user_id}."
        if chat_id:
            admin_msg = (
                f"Possible tampering/forgery attempt by user "
                f"{user_id} in chat {chat_id}."
            )

        super().__init__(
            status_code=400,
            user_message="Ошибка валидации подписи.",
            dev_message=f"PGP signature verification failed for user {user_id}.",
            admin_message=admin_msg
        )


class UserNotInGroupException(AppException):
    def __init__(self, chat_id: str, user_id: str):
        super().__init__(
            status_code=403,
            user_message="Вы не состоите в этой группе.",
            dev_message=(
                f"Access Denied: User {user_id} is not a member "
                f"of group chat {chat_id}."
            ),
            admin_message=(
                f"User {user_id} attempted to interact with group "
                f"{chat_id} without being a member."
            )
        )

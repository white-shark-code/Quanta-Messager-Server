"""WebSocket connection manager for realtime event notifications.

This module keeps in-memory WebSocket connections per user and
provides helpers to push notifications when new messages arrive.
Authentication reuses the same Bearer access tokens as the REST API
(``fastapi-users`` database strategy, ``SESSION_LIFETIME_SECONDS``), passed by the
client as ``?token=<access_token>`` query param because browsers
cannot set custom headers on WebSocket handshake.

Менеджер WebSocket-подключений для realtime-уведомлений о событиях.

Хранит соединения в памяти (user_id -> set[WebSocket]) и позволяет
пушить уведомления при новых сообщениях. Аутентификация переиспользует
те же Bearer-токены, что и REST API (database strategy,
``SESSION_LIFETIME_SECONDS``),
передаваемые как ``?token=<access_token>``, т.к. браузер не может
ставить кастомные заголовки при WebSocket-handshake.
"""

import asyncio
from typing import Any
from uuid import UUID

from fastapi import WebSocket
from fastapi_users.authentication.strategy.db import DatabaseStrategy
from fastapi_users_db_sqlalchemy import SQLAlchemyUserDatabase
from fastapi_users_db_sqlalchemy.access_token import SQLAlchemyAccessTokenDatabase

from authentication.models import AccessToken, User
from authentication.services import UserManager
from database import AsyncSession
from settings import cfg


class ConnectionManager:
    """In-memory mapping of user_id to active WebSocket connections.

    Хранит активные соединения user_id -> множество WebSocket.
    """

    def __init__(self) -> None:
        self._active: dict[UUID, set[WebSocket]] = {}
        self._lock: asyncio.Lock = asyncio.Lock()

    async def register(self, user_id: UUID, websocket: WebSocket) -> None:
        """Register an already-accepted socket for the user.

        Регистрирует уже принятое соединение за пользователем.
        """
        async with self._lock:
            self._active.setdefault(user_id, set()).add(websocket)

    async def connect(self, user_id: UUID, websocket: WebSocket) -> None:
        """Accept the socket and register it for the user.

        Принимает соединение и регистрирует его за пользователем.
        """
        await websocket.accept()
        await self.register(user_id, websocket)

    async def disconnect(self, user_id: UUID, websocket: WebSocket) -> None:
        """Remove the socket from the registry (idempotent).

        Удаляет сокет из реестра (идемпотентно).
        """
        async with self._lock:
            sockets = self._active.get(user_id)
            if sockets is not None:
                sockets.discard(websocket)
                if not sockets:
                    del self._active[user_id]

    def connection_count(self, user_id: UUID) -> int:
        """Return number of active sockets for the user (sync, for tests)."""
        return len(self._active.get(user_id, set()))

    async def send_to_user(self, user_id: UUID, message: dict[str, Any]) -> int:
        """Send a JSON message to all sockets of the user.

        Отправляет JSON-сообщение на все сокеты пользователя.
        Возвращает число сокетов, куда доставлено. Мёртвые сокеты
        молча удаляются. Никогда не бросает исключение наружу —
        доставка уведомлений best-effort и не должна ронять запрос.
        """
        async with self._lock:
            sockets = list(self._active.get(user_id, set()))
        delivered = 0
        for ws in sockets:
            try:
                await ws.send_json(message)
                delivered += 1
            except Exception:
                await self.disconnect(user_id, ws)
        return delivered


manager: ConnectionManager = ConnectionManager()


async def get_ws_user(token: str, session: AsyncSession) -> User | None:
    """Validate a Bearer token for a WebSocket handshake.

    Проверяет Bearer-токен при WebSocket-handshake через тот же
    DatabaseStrategy (тот же lifetime, что и REST API).

    Args:
        token: Raw access token string from ``?token=`` query param.
        session: Async database session.

    Returns:
        Authenticated active User, or None if token invalid/expired.
    """
    user_db = SQLAlchemyUserDatabase(session, User)
    user_manager = UserManager(user_db)
    access_token_db: SQLAlchemyAccessTokenDatabase[AccessToken] = (
        SQLAlchemyAccessTokenDatabase(session, AccessToken)
    )
    strategy = DatabaseStrategy(
        access_token_db, lifetime_seconds=cfg.SESSION_LIFETIME_SECONDS
    )
    try:
        user = await strategy.read_token(token, user_manager)
    except Exception:
        return None
    if user is None or not user.is_active:
        return None
    return user


def dialog_message_notification(
    chat_id: UUID, message_id: UUID, sender_id: UUID
) -> dict[str, Any]:
    """Build a new-dialog-message notification payload (IDs only, no ciphertext).

    Формирует payload уведомления о новом сообщении в диалоге
    (только ID, без шифротекста — клиент догрузит через REST).
    """
    return {
        "type": "new_dialog_message",
        "chat_id": str(chat_id),
        "message_id": str(message_id),
        "sender_id": str(sender_id),
    }


def group_message_notification(
    chat_id: UUID, message_id: UUID, sender_id: UUID
) -> dict[str, Any]:
    """Build a new-group-message notification payload (IDs only, no ciphertext).

    Формирует payload уведомления о новом сообщении в группе
    (только ID, без шифротекста — клиент догрузит через REST).
    """
    return {
        "type": "new_group_message",
        "chat_id": str(chat_id),
        "message_id": str(message_id),
        "sender_id": str(sender_id),
    }

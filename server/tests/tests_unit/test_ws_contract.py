"""Contract tests for the desktop-daemon WebSocket channel (no external services).

Контрактные тесты WebSocket-канала десктоп-демона (без внешних сервисов).

Covers the ``quantd`` daemon contract: ``?token=`` auth with ``4401`` close
semantics, ``ping`` -> ``pong`` keepalive, disconnect cleanup, and
multi-device fan-out to all sockets of one user.
"""

from types import SimpleNamespace
from uuid import uuid4

from fastapi import WebSocketDisconnect

import database
import events.router as events_router
from events.router import events_ws
from events.websocket import ConnectionManager


class FakeWebSocket:
    """Minimal in-memory WebSocket stand-in for contract tests.

    Минимальный in-memory стенд WebSocket для контрактных тестов.
    """

    def __init__(self, incoming: list[str] | None = None) -> None:
        self.incoming: list[str] = list(incoming or [])
        self.sent: list[dict] = []
        self.accepted = False
        self.close_code: int | None = None

    async def accept(self) -> None:
        self.accepted = True

    async def close(self, code: int = 1000) -> None:
        self.close_code = code

    async def send_json(self, message: dict) -> None:
        self.sent.append(message)

    async def receive_text(self) -> str:
        if self.incoming:
            return self.incoming.pop(0)
        raise WebSocketDisconnect()


class _FakeSession:
    """Async context manager yielding a dummy DB session.

    Async-контекстный менеджер, возвращающий фиктивную DB-сессию.
    """

    async def __aenter__(self) -> object:
        return object()

    async def __aexit__(self, *exc: object) -> bool:
        return False


def _patch_session_maker(monkeypatch) -> None:
    """Redirect the handshake DB session to a fake (no real DB).

    Подменяет DB-сессию handshake на фиктивную (без реальной БД).
    """
    monkeypatch.setattr(database, "_get_session_maker", lambda: lambda: _FakeSession())


def _patch_manager(monkeypatch) -> ConnectionManager:
    """Isolate tests from the global manager and return the fresh one.

    Изолирует тесты от глобального менеджера и возвращает свежий.
    """
    fresh = ConnectionManager()
    monkeypatch.setattr(events_router, "manager", fresh)
    return fresh


def _patch_ws_user(monkeypatch, user: object | None):
    """Mock token validation to return ``user`` (None = invalid/expired).

    Мокает проверку токена: возвращает ``user`` (None = невалиден/протух).
    """

    async def _fake_get_ws_user(token: str, session: object) -> object | None:
        assert token, "get_ws_user must receive the raw ?token= value"
        return user

    monkeypatch.setattr(events_router, "get_ws_user", _fake_get_ws_user)


async def test_no_token_closes_4401(monkeypatch) -> None:
    """Missing token closes the accepted socket with 4401.

    Отсутствие токена закрывает принятый сокет кодом 4401.
    """
    manager = _patch_manager(monkeypatch)
    ws = FakeWebSocket()

    await events_ws(ws, token=None)

    assert ws.accepted is True
    assert ws.close_code == 4401
    assert ws.sent == []
    assert manager.connection_count(uuid4()) == 0


async def test_invalid_token_closes_4401(monkeypatch) -> None:
    """Invalid token closes the accepted socket with 4401.

    Невалидный токен закрывает принятый сокет кодом 4401.
    """
    manager = _patch_manager(monkeypatch)
    _patch_session_maker(monkeypatch)
    _patch_ws_user(monkeypatch, None)
    ws = FakeWebSocket()

    await events_ws(ws, token="bad-token")

    assert ws.accepted is True
    assert ws.close_code == 4401
    assert ws.sent == []
    assert manager.connection_count(uuid4()) == 0


async def test_ping_returns_pong(monkeypatch) -> None:
    """Daemon keepalive ``ping`` gets ``{"type": "pong"}`` back.

    Keepalive демона ``ping`` получает в ответ ``{"type": "pong"}``.
    """
    manager = _patch_manager(monkeypatch)
    _patch_session_maker(monkeypatch)
    user_id = uuid4()
    _patch_ws_user(monkeypatch, SimpleNamespace(id=user_id))
    ws = FakeWebSocket(incoming=["ping"])

    await events_ws(ws, token="good-token")

    assert ws.accepted is True
    assert ws.close_code is None  # clean disconnect, not an auth kick
    assert ws.sent[0] == {"type": "connected", "user_id": str(user_id)}
    assert {"type": "pong"} in ws.sent
    assert manager.connection_count(user_id) == 0


async def test_disconnect_removes_socket_from_manager(monkeypatch) -> None:
    """Client disconnect removes its socket from the manager.

    Отключение клиента удаляет его сокет из менеджера.
    """
    manager = _patch_manager(monkeypatch)
    _patch_session_maker(monkeypatch)
    user_id = uuid4()
    _patch_ws_user(monkeypatch, SimpleNamespace(id=user_id))
    ws = FakeWebSocket(incoming=[])  # disconnects immediately

    await events_ws(ws, token="good-token")

    assert ws.close_code is None
    assert manager.connection_count(user_id) == 0


async def test_two_sockets_of_one_user_both_receive() -> None:
    """Two sockets of one user (UI + daemon) both get the push.

    Два сокета одного юзера (UI + демон) оба получают пуш.
    """
    manager = ConnectionManager()
    user_id = uuid4()
    ui_socket = FakeWebSocket()
    daemon_socket = FakeWebSocket()
    await manager.register(user_id, ui_socket)
    await manager.register(user_id, daemon_socket)
    assert manager.connection_count(user_id) == 2

    payload = {"type": "new_dialog_message", "chat_id": "abc"}
    delivered = await manager.send_to_user(user_id, payload)

    assert delivered == 2
    assert ui_socket.sent == [payload]
    assert daemon_socket.sent == [payload]

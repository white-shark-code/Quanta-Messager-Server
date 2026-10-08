"""Live Redis notifications end-to-end test (requires Redis, no DB needed).

This module verifies the full chain over a real Redis server:
``publish_event`` -> Redis ``events`` channel -> ``subscriber`` ->
``manager.send_to_user`` -> local socket. It uses fake in-memory
sockets, so no database is required. The DB-heavy autouse fixtures
from ``tests_integration/conftest.py`` are shadowed with no-ops on
purpose: this test must skip (not hang) when the database is down.

Сквозной тест уведомлений через живой Redis (нужен Redis, БД не нужна).

Модуль проверяет полную цепочку через реальный Redis:
``publish_event`` -> Redis-канал ``events`` -> ``subscriber`` ->
``manager.send_to_user`` -> локальный сокет. Используются фейковые
in-memory сокеты, поэтому база данных не требуется. Тяжёлые
autouse-фикстуры БД из ``tests_integration/conftest.py`` здесь
намеренно перекрыты заглушками: тест должен скипаться (а не висеть),
когда база недоступна.
"""

import asyncio
import contextlib
import os
from collections.abc import AsyncGenerator, Generator
from typing import Any
from uuid import UUID, uuid4

import pytest
import pytest_asyncio
import redis.asyncio as redis

from events import bus
from events.bus import CHANNEL, decode_event, publish_event
from events.websocket import manager


@pytest.fixture(scope="session", autouse=True)
def apply_migrations() -> Generator[None]:
    """No-op shadow: this e2e needs no DB migrations.

    Заглушка: этому e2e не нужны миграции БД.
    """
    yield


@pytest_asyncio.fixture(scope="session", autouse=True, loop_scope="session")
async def seed_users() -> AsyncGenerator[None]:
    """No-op shadow: no users need seeding without a DB.

    Заглушка: без БД сидировать пользователей не нужно.
    """
    yield


@pytest_asyncio.fixture(autouse=True, loop_scope="session")
async def clean_db_before_test() -> AsyncGenerator[None]:
    """No-op shadow: nothing to truncate without a DB.

    Заглушка: без БД чистить таблицы не нужно.
    """
    yield


@pytest_asyncio.fixture(autouse=True, loop_scope="session")
async def override_get_async_session() -> AsyncGenerator[None]:
    """No-op shadow: endpoints are not touched in this e2e.

    Заглушка: эндпоинты в этом e2e не вызываются.
    """
    yield


def _redis_url() -> str:
    """Return the Redis URL for the live check (env wins, then app cfg).

    Возвращает Redis URL для живой проверки (сначала env, потом cfg).
    """
    return os.getenv("REDIS_URL", "").strip() or bus.cfg.REDIS_URL


_needs_redis = pytest.mark.skipif(
    not os.getenv("REDIS_URL"),
    reason="REDIS_URL is not set — live Redis e2e skipped (CI without Redis)",
)


class _FakeSocket:
    """In-memory WebSocket stand-in collecting sent JSON messages.

    In-memory стенд WebSocket, собирающий отправленные JSON-сообщения.
    """

    def __init__(self) -> None:
        self.sent: list[dict[str, Any]] = []

    async def send_json(self, message: dict[str, Any]) -> None:
        """Collect one outgoing JSON message.

        Сохраняет одно исходящее JSON-сообщение.
        """
        self.sent.append(message)


async def _probe_redis(url: str) -> None:
    """Ping Redis with a short timeout, skip the test if unreachable.

    Пингует Redis с коротким таймаутом, скипает тест если недоступен.
    """
    probe = redis.from_url(
        url, socket_connect_timeout=2, socket_timeout=2, decode_responses=True
    )
    try:
        await asyncio.wait_for(probe.ping(), timeout=3)
    except Exception as exc:
        pytest.skip(f"Redis unavailable, live e2e skipped: {type(exc).__name__}")
    finally:
        with contextlib.suppress(Exception):
            await probe.aclose()


@_needs_redis
async def test_notifications_e2e_publish_subscriber_fanout(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Publish -> subscriber -> manager.send_to_user reaches the socket.

    Проверяет, что publish доходит через подписчика до сокета менеджера,
    а чужому пользователю ничего не приходит. Только ID в payload.
    """
    url = _redis_url()
    await _probe_redis(url)
    monkeypatch.setattr(bus.cfg, "REDIS_URL", url)

    user_id: UUID = uuid4()
    stranger_id: UUID = uuid4()
    socket = _FakeSocket()
    stranger_socket = _FakeSocket()
    await manager.register(user_id, socket)  # type: ignore[arg-type]
    await manager.register(stranger_id, stranger_socket)  # type: ignore[arg-type]

    stop = asyncio.Event()
    task = asyncio.create_task(bus.subscriber(stop))
    try:
        payload = {
            "type": "new_dialog_message",
            "chat_id": str(uuid4()),
            "message_id": str(uuid4()),
            "sender_id": str(uuid4()),
        }
        deadline = asyncio.get_running_loop().time() + 7.0
        while not socket.sent and asyncio.get_running_loop().time() < deadline:
            await publish_event([user_id], payload)
            await asyncio.sleep(0.5)

        assert socket.sent, "subscriber did not fan out the bus message in time"
        assert socket.sent[0] == payload
        assert stranger_socket.sent == []
    finally:
        stop.set()
        task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await task
        await manager.disconnect(user_id, socket)  # type: ignore[arg-type]
        await manager.disconnect(stranger_id, stranger_socket)  # type: ignore[arg-type]


@_needs_redis
async def test_notifications_e2e_envelope_format_over_redis(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Raw envelope on the ``events`` channel decodes to recipients+payload.

    Проверяет сырой конверт в канале ``events``: декодируется
    в получателей и payload через ``decode_event``.
    """
    url = _redis_url()
    await _probe_redis(url)
    monkeypatch.setattr(bus.cfg, "REDIS_URL", url)

    recipients = [uuid4()]
    payload = {"type": "new_group_message", "chat_id": str(uuid4())}
    reader = redis.from_url(
        url, socket_connect_timeout=2, socket_timeout=2, decode_responses=True
    )
    pubsub = reader.pubsub()
    try:
        await pubsub.subscribe(CHANNEL)
        await asyncio.sleep(0.5)
        await publish_event(recipients, payload)
        # NOTE: asyncio get_message(timeout=...) is a socket timeout, not a
        # wait: it returns None when nothing is buffered yet, and a message
        # dict (not the raw data) when one arrived. Poll briefly instead.
        raw: str | bytes | None = None
        deadline = asyncio.get_running_loop().time() + 7.0
        while raw is None and asyncio.get_running_loop().time() < deadline:
            message = await pubsub.get_message(
                ignore_subscribe_messages=True, timeout=1.0
            )
            if isinstance(message, dict):
                data = message.get("data")
                if isinstance(data, str | bytes):
                    raw = data
                    break
            await asyncio.sleep(0.2)
        assert raw is not None, "no raw message arrived on the events channel"
        parsed_recipients, parsed_payload = decode_event(raw)
        assert parsed_recipients == recipients
        assert parsed_payload == payload
    finally:
        with contextlib.suppress(Exception):
            await pubsub.unsubscribe(CHANNEL)
        with contextlib.suppress(Exception):
            await reader.aclose()

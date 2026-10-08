"""Unit tests for WebSocket notifications (no DB required).

Юнит-тесты WebSocket-уведомлений (БД не требуется).
"""

from unittest.mock import AsyncMock
from uuid import uuid4

from events.websocket import (
    ConnectionManager,
    dialog_message_notification,
    group_message_notification,
)


class TestConnectionManager:
    async def test_connect_and_send_to_user(self):
        manager = ConnectionManager()
        user_id = uuid4()
        ws = AsyncMock()
        await manager.connect(user_id, ws)
        ws.accept.assert_awaited_once()
        assert manager.connection_count(user_id) == 1

        payload = {"type": "ping-test"}
        delivered = await manager.send_to_user(user_id, payload)
        assert delivered == 1
        ws.send_json.assert_awaited_once_with(payload)

    async def test_disconnect_removes_socket(self):
        manager = ConnectionManager()
        user_id = uuid4()
        ws = AsyncMock()
        await manager.connect(user_id, ws)
        await manager.disconnect(user_id, ws)
        assert manager.connection_count(user_id) == 0
        delivered = await manager.send_to_user(user_id, {"type": "x"})
        assert delivered == 0

    async def test_dead_socket_evicted(self):
        manager = ConnectionManager()
        user_id = uuid4()
        dead = AsyncMock()
        dead.send_json.side_effect = RuntimeError("gone")
        alive = AsyncMock()
        await manager.connect(user_id, dead)
        await manager.connect(user_id, alive)

        delivered = await manager.send_to_user(user_id, {"type": "x"})
        assert delivered == 1
        assert manager.connection_count(user_id) == 1

    async def test_send_to_unknown_user(self):
        manager = ConnectionManager()
        assert await manager.send_to_user(uuid4(), {"type": "x"}) == 0


class TestNotificationPayloads:
    def test_dialog_payload_has_ids_only(self):
        chat_id, msg_id, sender_id = uuid4(), uuid4(), uuid4()
        payload = dialog_message_notification(chat_id, msg_id, sender_id)
        assert payload == {
            "type": "new_dialog_message",
            "chat_id": str(chat_id),
            "message_id": str(msg_id),
            "sender_id": str(sender_id),
        }
        assert "encrypted_message" not in payload

    def test_group_payload_has_ids_only(self):
        chat_id, msg_id, sender_id = uuid4(), uuid4(), uuid4()
        payload = group_message_notification(chat_id, msg_id, sender_id)
        assert payload["type"] == "new_group_message"
        assert payload["chat_id"] == str(chat_id)
        assert "encrypted_message" not in payload

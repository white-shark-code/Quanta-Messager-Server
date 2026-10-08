"""Unit tests for the Redis event bus (no external services).

Юнит-тесты Redis-шины событий (без внешних сервисов).
"""

import asyncio
import json
import logging
from unittest.mock import AsyncMock
from uuid import uuid4

from events import bus
from events.bus import (
    CHANNEL,
    WARN_AFTER_FAILURES,
    _redact_url,
    _reset_bus_failures,
    decode_event,
    encode_event,
    handle_message,
    publish_event,
)


class FakePublisher:
    """In-memory stand-in for the redis asyncio client (publish side)."""

    def __init__(self) -> None:
        self.published: list[tuple[str, str]] = []
        self.closed = False

    async def publish(self, channel: str, message: str) -> int:
        self.published.append((channel, message))
        return 1

    async def aclose(self) -> None:
        self.closed = True


class TestEnvelopeSerialization:
    def test_encode_produces_channel_payload_shape(self):
        recipients = [uuid4(), uuid4()]
        payload = {"type": "new_dialog_message", "chat_id": "abc"}
        raw = encode_event(recipients, payload)
        data = json.loads(raw)
        assert set(data.keys()) == {"recipients", "payload"}
        assert data["recipients"] == [str(uid) for uid in recipients]
        assert data["payload"] == payload

    def test_decode_roundtrip(self):
        recipients = [uuid4(), uuid4()]
        payload = {"type": "new_group_message", "chat_id": "xyz"}
        parsed_recipients, parsed_payload = decode_event(
            encode_event(recipients, payload)
        )
        assert parsed_recipients == recipients
        assert parsed_payload == payload


class TestHandleMessage:
    async def test_delivers_to_each_recipient(self, monkeypatch):
        recipients = [uuid4(), uuid4()]
        payload = {"type": "ping-test"}
        send_mock = AsyncMock(return_value=1)
        monkeypatch.setattr(bus.manager, "send_to_user", send_mock)

        await handle_message(encode_event(recipients, payload))

        assert send_mock.await_count == len(recipients)
        for user_id in recipients:
            send_mock.assert_any_await(user_id, payload)

    async def test_malformed_message_never_raises(self, monkeypatch):
        send_mock = AsyncMock()
        monkeypatch.setattr(bus.manager, "send_to_user", send_mock)

        for bad in ("not-json", '{"recipients": "nope"}', None, b"\xff\xfe"):
            await handle_message(bad)  # must not raise

        send_mock.assert_not_awaited()


class TestPublishEvent:
    async def test_publish_uses_events_channel(self, monkeypatch):
        fake = FakePublisher()
        monkeypatch.setattr(
            bus.redis, "from_url", lambda *args, **kwargs: fake
        )
        recipients = [uuid4()]
        payload = {"type": "new_dialog_message"}

        await publish_event(recipients, payload)

        assert len(fake.published) == 1
        channel, raw = fake.published[0]
        assert channel == CHANNEL == "events"
        data = json.loads(raw)
        assert data == {
            "recipients": [str(recipients[0])],
            "payload": payload,
        }
        assert fake.closed is True

    async def test_publish_does_not_raise_when_redis_down(self, monkeypatch):
        def _raise(*args, **kwargs):
            raise ConnectionError("redis unavailable")

        monkeypatch.setattr(bus.redis, "from_url", _raise)

        await publish_event([uuid4()], {"type": "x"})  # must not raise

    async def test_publish_does_not_raise_when_publish_fails(self, monkeypatch):
        class FailingPublisher(FakePublisher):
            async def publish(self, channel: str, message: str) -> int:
                raise ConnectionError("publish failed")

        monkeypatch.setattr(
            bus.redis, "from_url", lambda *args, **kwargs: FailingPublisher()
        )

        await publish_event([uuid4()], {"type": "x"})  # must not raise


class TestSubscriber:
    async def test_fans_out_bus_message_to_local_manager(self, monkeypatch):
        recipients = [uuid4(), uuid4()]
        payload = {"type": "new_dialog_message", "chat_id": "abc"}
        raw = encode_event(recipients, payload)
        send_mock = AsyncMock(return_value=1)
        monkeypatch.setattr(bus.manager, "send_to_user", send_mock)

        class FakePubSub:
            async def subscribe(self, channel: str) -> None:
                assert channel == CHANNEL

            async def listen(self):
                yield {"type": "subscribe", "channel": CHANNEL, "data": 1}
                yield {"type": "message", "channel": CHANNEL, "data": raw}
                await asyncio.Future()  # hang until the task is cancelled

        class FakeClient:
            def pubsub(self) -> FakePubSub:
                return FakePubSub()

            async def aclose(self) -> None:
                return None

        monkeypatch.setattr(
            bus.redis, "from_url", lambda *args, **kwargs: FakeClient()
        )

        task = asyncio.create_task(bus.subscriber())
        try:
            for _ in range(200):
                if send_mock.await_count >= len(recipients):
                    break
                await asyncio.sleep(0.01)
            assert send_mock.await_count == len(recipients)
            for user_id in recipients:
                send_mock.assert_any_await(user_id, payload)
        finally:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass


class TestRedactUrl:
    def test_password_is_hidden(self):
        redacted = _redact_url("redis://:s3cret@192.168.1.50:6381/0")
        assert "s3cret" not in redacted
        assert "192.168.1.50" in redacted
        assert "6381" in redacted
        assert "***" in redacted

    def test_url_without_password_unchanged(self):
        url = "redis://localhost:6379/0"
        assert _redact_url(url) == url

    def test_garbage_never_raises(self):
        assert isinstance(_redact_url("not a url at all"), str)
        assert isinstance(_redact_url(""), str)


class TestFailureSignals:
    def setup_method(self):
        _reset_bus_failures()

    async def test_warn_after_streak_of_publish_failures(
        self, monkeypatch, caplog
    ):
        def _raise(*args, **kwargs):
            raise ConnectionError("redis unavailable")

        monkeypatch.setattr(bus.redis, "from_url", _raise)

        with caplog.at_level(logging.DEBUG, logger="events.bus"):
            for _ in range(WARN_AFTER_FAILURES - 1):
                await publish_event([uuid4()], {"type": "x"})
            assert not [r for r in caplog.records if r.levelno >= logging.WARNING]

            await publish_event([uuid4()], {"type": "x"})
            warnings = [r for r in caplog.records if r.levelno >= logging.WARNING]
            assert len(warnings) == 1
            assert "publish" in warnings[0].getMessage()

    async def test_success_resets_publish_streak(self, monkeypatch, caplog):
        calls = {"n": 0}

        def _flaky(*args, **kwargs):
            calls["n"] += 1
            if calls["n"] <= WARN_AFTER_FAILURES:
                raise ConnectionError("down")
            return FakePublisher()

        monkeypatch.setattr(bus.redis, "from_url", _flaky)

        with caplog.at_level(logging.DEBUG, logger="events.bus"):
            for _ in range(WARN_AFTER_FAILURES):
                await publish_event([uuid4()], {"type": "x"})
            assert [r for r in caplog.records if r.levelno >= logging.WARNING]
            caplog.clear()

            await publish_event([uuid4()], {"type": "x"})  # success, streak reset
            await publish_event([uuid4()], {"type": "x"})  # would fail? no: now ok
            assert not [r for r in caplog.records if r.levelno >= logging.WARNING]

    def test_subscriber_streak_warns_and_hides_password(
        self, monkeypatch, caplog
    ):
        monkeypatch.setattr(
            bus.cfg, "REDIS_URL", "redis://:s3cret@192.168.1.50:6381/0"
        )
        with caplog.at_level(logging.DEBUG, logger="events.bus"):
            for _ in range(WARN_AFTER_FAILURES):
                bus._note_failure("subscriber", ConnectionError("auth"))
            warnings = [r for r in caplog.records if r.levelno >= logging.WARNING]
            assert warnings
            for record in caplog.records:
                assert "s3cret" not in record.getMessage()

    def test_note_success_resets_counter(self):
        bus._note_failure("publish", ConnectionError("x"))
        assert bus._failures["publish"] == 1
        bus._note_success("publish")
        assert bus._failures["publish"] == 0

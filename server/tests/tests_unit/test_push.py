"""Unit tests for Web Push subscriptions and delivery (no external services).

All ``pywebpush`` network calls are mocked; database access is covered
with scripted fake sessions at the service layer (router status codes
are checked with stubbed service functions).

Юнит-тесты подписок Web Push и доставки (без внешних сервисов).

Все сетевые вызовы ``pywebpush`` замоканы; доступ к БД покрыт
скриптованными фейк-сессиями на уровне сервисов (коды статусов
роутера проверены со стабами сервисных функций).
"""

import json
from types import SimpleNamespace
from uuid import uuid4

from fastapi import Response
from pywebpush import WebPushException

import push.router as push_router
import push.services as push_services
from push.schemas import PushSubscribeRequest, PushUnsubscribeRequest
from push.services import (
    delete_subscription,
    delete_subscription_by_endpoint,
    dialog_push_payload,
    get_subscriptions_for_users,
    group_push_payload,
    send_push_to_users,
    upsert_subscription,
)
from settings import cfg

ENDPOINT = "https://push.example.com/sub/abc123"


class FakeResult:
    """Scripted stand-in for a SQLAlchemy result object."""

    def __init__(self, one=None, many=None) -> None:
        self._one = one
        self._many = many

    def scalar_one_or_none(self):
        return self._one

    def scalars(self):
        outer = self

        class _Scalars:
            def all(self):
                return list(outer._many or [])

        return _Scalars()


class FakeSession:
    """Scripted stand-in for an AsyncSession."""

    def __init__(self, results=()) -> None:
        self._results = list(results)
        self.statements = []
        self.added = []
        self.deleted = []
        self.commits = 0

    async def execute(self, stmt):
        self.statements.append(stmt)
        return self._results.pop(0)

    def add(self, obj) -> None:
        self.added.append(obj)

    async def delete(self, obj) -> None:
        self.deleted.append(obj)

    async def commit(self) -> None:
        self.commits += 1


def _where_mapping(stmt):
    """Map filtered column names to bound values of a select statement."""
    clause = stmt.whereclause
    criteria = clause.clauses if hasattr(clause, "clauses") else (clause,)
    return {criterion.left.key: criterion.right.value for criterion in criteria}


def _gone_response(status_code):
    return SimpleNamespace(status_code=status_code, headers={}, text="")


class TestPushPayloads:
    def test_dialog_payload_has_ids_only(self):
        chat_id, message_id = uuid4(), uuid4()
        assert dialog_push_payload(chat_id, message_id) == {
            "type": "new_dialog_message",
            "chat_id": str(chat_id),
            "message_id": str(message_id),
        }

    def test_group_payload_has_ids_only(self):
        chat_id, message_id = uuid4(), uuid4()
        payload = group_push_payload(chat_id, message_id)
        assert payload["type"] == "new_group_message"
        assert payload["chat_id"] == str(chat_id)
        assert payload["message_id"] == str(message_id)
        assert "sender_id" not in payload
        assert "encrypted_message" not in payload
        assert not any("name" in key for key in payload)


class TestUpsertSubscription:
    async def test_creates_when_missing(self):
        session = FakeSession(results=[FakeResult(one=None)])
        user_id = uuid4()

        subscription, created = await upsert_subscription(
            session, user_id, ENDPOINT, "p256dh-1", "auth-1"
        )

        assert created is True
        assert subscription.user_id == user_id
        assert subscription.endpoint == ENDPOINT
        assert subscription.p256dh == "p256dh-1"
        assert subscription.auth == "auth-1"
        assert session.added == [subscription]

    async def test_updates_keys_when_exists(self):
        existing = SimpleNamespace(
            user_id=uuid4(), endpoint=ENDPOINT, p256dh="old", auth="old"
        )
        session = FakeSession(results=[FakeResult(one=existing)])

        subscription, created = await upsert_subscription(
            session, existing.user_id, ENDPOINT, "p256dh-2", "auth-2"
        )

        assert created is False
        assert subscription is existing
        assert existing.p256dh == "p256dh-2"
        assert existing.auth == "auth-2"
        assert session.added == []

    async def test_lookup_scoped_to_user_and_endpoint(self):
        session = FakeSession(results=[FakeResult(one=None)])
        user_id = uuid4()

        await upsert_subscription(session, user_id, ENDPOINT, "p", "a")

        assert _where_mapping(session.statements[0]) == {
            "user_id": user_id,
            "endpoint": ENDPOINT,
        }


class TestDeleteSubscription:
    async def test_deletes_own_subscription(self):
        existing = SimpleNamespace(user_id=uuid4(), endpoint=ENDPOINT)
        session = FakeSession(results=[FakeResult(one=existing)])

        assert await delete_subscription(session, existing.user_id, ENDPOINT) is True
        assert session.deleted == [existing]

    async def test_missing_subscription_is_idempotent(self):
        session = FakeSession(results=[FakeResult(one=None)])

        assert await delete_subscription(session, uuid4(), ENDPOINT) is False
        assert session.deleted == []

    async def test_delete_scoped_to_user_and_endpoint(self):
        session = FakeSession(results=[FakeResult(one=None)])
        user_id = uuid4()

        await delete_subscription(session, user_id, ENDPOINT)

        assert _where_mapping(session.statements[0]) == {
            "user_id": user_id,
            "endpoint": ENDPOINT,
        }

    async def test_delete_by_endpoint_ignores_owner(self):
        existing = SimpleNamespace(user_id=uuid4(), endpoint=ENDPOINT)
        session = FakeSession(results=[FakeResult(one=existing)])

        assert await delete_subscription_by_endpoint(session, ENDPOINT) is True
        assert session.deleted == [existing]
        assert _where_mapping(session.statements[0]) == {"endpoint": ENDPOINT}


class TestGetSubscriptions:
    async def test_returns_all_user_subscriptions(self):
        subs = [
            SimpleNamespace(endpoint=f"https://push.example.com/{i}")
            for i in range(2)
        ]
        session = FakeSession(results=[FakeResult(many=subs)])

        assert await get_subscriptions_for_users(session, [uuid4()]) == subs


class TestSendPushToUsers:
    async def test_skipped_when_vapid_not_configured(self, monkeypatch):
        monkeypatch.setattr(cfg, "VAPID_PRIVATE_KEY", "")
        monkeypatch.setattr(cfg, "VAPID_CLAIMS_SUB", "")
        calls = []

        def _record_webpush(**kwargs):
            calls.append(kwargs)

        monkeypatch.setattr(push_services, "webpush", _record_webpush)
        session = FakeSession(results=[FakeResult(many=[SimpleNamespace()])])

        await send_push_to_users(session, [uuid4()], {"type": "x"})

        assert calls == []
        assert session.statements == []

    async def test_sends_id_only_payload(self, monkeypatch):
        monkeypatch.setattr(cfg, "VAPID_PRIVATE_KEY", "test-private-key")
        monkeypatch.setattr(cfg, "VAPID_CLAIMS_SUB", "mailto:test@localhost")
        calls = []

        def _fake_webpush(**kwargs):
            calls.append(kwargs)

        monkeypatch.setattr(push_services, "webpush", _fake_webpush)
        sub = SimpleNamespace(endpoint=ENDPOINT, p256dh="p256dh-1", auth="auth-1")
        session = FakeSession(results=[FakeResult(many=[sub])])
        chat_id, message_id = uuid4(), uuid4()

        await send_push_to_users(
            session, [uuid4()], dialog_push_payload(chat_id, message_id)
        )

        assert len(calls) == 1
        assert calls[0]["subscription_info"] == {
            "endpoint": ENDPOINT,
            "keys": {"p256dh": "p256dh-1", "auth": "auth-1"},
        }
        assert json.loads(calls[0]["data"]) == {
            "type": "new_dialog_message",
            "chat_id": str(chat_id),
            "message_id": str(message_id),
        }
        assert calls[0]["ttl"] == 2419200
        assert calls[0]["headers"] == {"Urgency": "normal"}
        assert calls[0]["vapid_private_key"] == "test-private-key"
        assert calls[0]["vapid_claims"] == {"sub": "mailto:test@localhost"}
        assert session.deleted == []

    async def test_gone_endpoint_is_cleaned_up(self, monkeypatch):
        monkeypatch.setattr(cfg, "VAPID_PRIVATE_KEY", "test-private-key")
        monkeypatch.setattr(cfg, "VAPID_CLAIMS_SUB", "mailto:test@localhost")

        def _fake_webpush(**kwargs):
            raise WebPushException("gone", response=_gone_response(410))

        monkeypatch.setattr(push_services, "webpush", _fake_webpush)
        sub = SimpleNamespace(endpoint=ENDPOINT, p256dh="p", auth="a")
        session = FakeSession(
            results=[
                FakeResult(many=[sub]),
                FakeResult(one=sub),
            ]
        )

        await send_push_to_users(session, [uuid4()], {"type": "new_group_message"})

        assert session.deleted == [sub]
        assert session.commits == 1

    async def test_transient_failure_keeps_subscription(self, monkeypatch):
        monkeypatch.setattr(cfg, "VAPID_PRIVATE_KEY", "test-private-key")
        monkeypatch.setattr(cfg, "VAPID_CLAIMS_SUB", "mailto:test@localhost")

        def _fake_webpush(**kwargs):
            raise WebPushException("boom", response=_gone_response(500))

        monkeypatch.setattr(push_services, "webpush", _fake_webpush)
        session = FakeSession(
            results=[
                FakeResult(
                    many=[SimpleNamespace(endpoint=ENDPOINT, p256dh="p", auth="a")]
                )
            ]
        )

        await send_push_to_users(session, [uuid4()], {"type": "x"})  # must not raise

        assert session.deleted == []
        assert session.commits == 0

    async def test_lookup_failure_never_raises(self, monkeypatch):
        monkeypatch.setattr(cfg, "VAPID_PRIVATE_KEY", "test-private-key")
        monkeypatch.setattr(cfg, "VAPID_CLAIMS_SUB", "mailto:test@localhost")
        monkeypatch.setattr(push_services, "webpush", lambda **kwargs: None)

        class _FailingSession(FakeSession):
            async def execute(self, stmt):
                raise ConnectionError("db down")

        await send_push_to_users(_FailingSession(), [uuid4()], {"type": "x"})


class TestPushRouterStatuses:
    async def test_subscribe_returns_201_then_200(self, monkeypatch):
        store = {}

        async def _fake_upsert(session, user_id, endpoint, p256dh, auth):
            created = (user_id, endpoint) not in store
            store[(user_id, endpoint)] = (p256dh, auth)
            return SimpleNamespace(endpoint=endpoint), created

        monkeypatch.setattr(push_router, "upsert_subscription", _fake_upsert)
        user = SimpleNamespace(id=uuid4())
        session = FakeSession()
        body = {"endpoint": ENDPOINT, "keys": {"p256dh": "p1", "auth": "a1"}}

        first = Response()
        await push_router.subscribe_push(
            PushSubscribeRequest(**body), first, user, session
        )
        assert first.status_code == 201

        second = Response()
        await push_router.subscribe_push(
            PushSubscribeRequest(
                endpoint=ENDPOINT, keys={"p256dh": "p2", "auth": "a2"}
            ),
            second,
            user,
            session,
        )
        assert second.status_code == 200
        assert store[(user.id, ENDPOINT)] == ("p2", "a2")
        assert session.commits == 2

    async def test_unsubscribe_idempotent_and_keeps_others(self, monkeypatch):
        store = {}

        async def _fake_delete(session, user_id, endpoint):
            return store.pop((user_id, endpoint), None) is not None

        monkeypatch.setattr(push_router, "delete_subscription", _fake_delete)
        user_id, other_id = uuid4(), uuid4()
        store[(user_id, ENDPOINT)] = ("p", "a")
        store[(other_id, "https://push.example.com/other")] = ("p", "a")
        user = SimpleNamespace(id=user_id)
        session = FakeSession()

        first = await push_router.unsubscribe_push(
            PushUnsubscribeRequest(endpoint=ENDPOINT), user, session
        )
        assert first.status_code == 204

        second = await push_router.unsubscribe_push(
            PushUnsubscribeRequest(endpoint=ENDPOINT), user, session
        )
        assert second.status_code == 204

        foreign = await push_router.unsubscribe_push(
            PushUnsubscribeRequest(endpoint="https://push.example.com/other"),
            user,
            session,
        )
        assert foreign.status_code == 204
        assert (other_id, "https://push.example.com/other") in store
        assert session.commits == 3

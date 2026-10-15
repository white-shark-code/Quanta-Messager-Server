"""Unit tests for the shared session lifetime (no external services).

Юнит-тесты общего времени жизни сессии (без внешних сервисов).
"""

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import authentication.services as auth_services
import events.websocket as ws
from settings import cfg


class TestSessionLifetime:
    def test_rest_strategy_uses_configured_lifetime(self, monkeypatch):
        captured: dict = {}

        def _fake_strategy(db, lifetime_seconds):
            captured["lifetime_seconds"] = lifetime_seconds
            return MagicMock()

        monkeypatch.setattr(auth_services, "DatabaseStrategy", _fake_strategy)
        auth_services.get_database_strategy(access_token_db=MagicMock())
        assert captured["lifetime_seconds"] == cfg.SESSION_LIFETIME_SECONDS
        assert captured["lifetime_seconds"] == 2592000

    async def test_ws_strategy_uses_configured_lifetime(self, monkeypatch):
        captured: dict = {}

        def _fake_strategy(db, lifetime_seconds):
            captured["lifetime_seconds"] = lifetime_seconds
            strategy = MagicMock()
            strategy.read_token = AsyncMock(
                return_value=SimpleNamespace(is_active=True)
            )
            return strategy

        monkeypatch.setattr(ws, "DatabaseStrategy", _fake_strategy)
        monkeypatch.setattr(ws, "SQLAlchemyUserDatabase", MagicMock())
        monkeypatch.setattr(ws, "SQLAlchemyAccessTokenDatabase", MagicMock())
        monkeypatch.setattr(ws, "UserManager", MagicMock())

        user = await ws.get_ws_user(token="tok", session=MagicMock())
        assert user is not None
        assert user.is_active is True
        assert captured["lifetime_seconds"] == cfg.SESSION_LIFETIME_SECONDS

    def test_rest_and_ws_share_one_setting(self):
        assert cfg.SESSION_LIFETIME_SECONDS >= 30 * 24 * 3600

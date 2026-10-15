"""Unit tests for the health endpoint (no external services).

Юнит-тесты health-эндпоинта (без внешних сервисов).
"""

from unittest.mock import AsyncMock

from fastapi import FastAPI
from fastapi.testclient import TestClient

import health
from health import check_database, check_redis, health_router


def _client() -> TestClient:
    app = FastAPI()
    app.include_router(health_router)
    return TestClient(app)


class TestChecks:
    async def test_check_database_false_when_down(self, monkeypatch):
        def _raise():
            raise ConnectionError("db down")

        monkeypatch.setattr(health, "_get_session_maker", _raise)
        assert await check_database() is False

    async def test_check_redis_false_when_down(self, monkeypatch):
        def _raise(*args, **kwargs):
            raise ConnectionError("redis down")

        monkeypatch.setattr(health.redis, "from_url", _raise)
        assert await check_redis() is False


class TestEndpoint:
    def test_all_up_returns_200_ok(self, monkeypatch):
        monkeypatch.setattr(health, "check_database", AsyncMock(return_value=True))
        monkeypatch.setattr(health, "check_redis", AsyncMock(return_value=True))
        response = _client().get("/health")
        assert response.status_code == 200
        assert response.json() == {
            "status": "ok",
            "database": "up",
            "redis": "up",
        }

    def test_any_down_returns_503_degraded(self, monkeypatch):
        monkeypatch.setattr(health, "check_database", AsyncMock(return_value=True))
        monkeypatch.setattr(health, "check_redis", AsyncMock(return_value=False))
        response = _client().get("/health")
        assert response.status_code == 503
        body = response.json()
        assert body["status"] == "degraded"
        assert body["redis"] == "down"

    def test_endpoint_never_raises(self, monkeypatch):
        async def _boom():
            raise RuntimeError("unexpected")

        monkeypatch.setattr(health, "check_database", _boom)
        monkeypatch.setattr(health, "check_redis", _boom)
        # check_* never raise by contract, endpoint must still answer
        response = _client().get("/health")
        assert response.status_code == 503

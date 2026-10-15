"""Health check endpoint for liveness and dependency probes.

This module exposes an unauthenticated ``GET /health`` endpoint used by
load balancers, docker healthchecks and monitoring. It reports the app
itself plus its mandatory dependencies (database, Redis event bus).
The endpoint never raises and never hangs: every check runs with a
short timeout and failures are reported as ``"down"`` in the payload.

Health-эндпоинт для liveness-проб и мониторинга зависимостей.

Модуль отдаёт неавторизованный ``GET /health`` для балансировщиков,
docker-healthcheck и мониторинга. Проверяет само приложение и
обязательные зависимости (БД, Redis-шина). Эндпоинт никогда не
бросает исключений и не висит: каждая проверка с коротким таймаутом,
неисправности отражаются как ``"down"`` в ответе.
"""

import asyncio

import redis.asyncio as redis
from fastapi import APIRouter
from fastapi.responses import JSONResponse
from sqlalchemy import text

from database import _get_session_maker
from settings import cfg

health_router: APIRouter = APIRouter()

_CHECK_TIMEOUT: float = 3.0


async def check_database() -> bool:
    """Return True if a trivial DB query succeeds within the timeout.

    Возвращает True, если тривиальный запрос к БД успешен в пределах таймаута.
    Never raises.
    """
    try:
        async with _get_session_maker()() as session:
            await asyncio.wait_for(session.execute(text("SELECT 1")), _CHECK_TIMEOUT)
        return True
    except Exception:
        return False


async def check_redis() -> bool:
    """Return True if Redis answers PING within the timeout.

    Возвращает True, если Redis отвечает на PING в пределах таймаута.
    Never raises.
    """
    client = None
    try:
        client = redis.from_url(
            cfg.REDIS_URL,
            socket_connect_timeout=_CHECK_TIMEOUT,
            socket_timeout=_CHECK_TIMEOUT,
            decode_responses=True,
        )
        await asyncio.wait_for(client.ping(), _CHECK_TIMEOUT)
        return True
    except Exception:
        return False
    finally:
        if client is not None:
            try:
                await client.aclose()
            except Exception:
                pass


@health_router.get(path="/health")
async def health() -> JSONResponse:
    """Report liveness and dependency status.

    Отдаёт статус живости и зависимостей. HTTP 200 — всё доступно,
    HTTP 503 — хотя бы одна зависимость недоступна.
    """
    database_up, redis_up = (False, False)
    try:
        database_up, redis_up = await asyncio.gather(check_database(), check_redis())
    except Exception:
        pass
    all_up = database_up and redis_up
    return JSONResponse(
        status_code=200 if all_up else 503,
        content={
            "status": "ok" if all_up else "degraded",
            "database": "up" if database_up else "down",
            "redis": "up" if redis_up else "down",
        },
    )

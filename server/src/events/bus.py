"""Redis event bus for WebSocket notifications across workers.

This module publishes realtime notification envelopes to a Redis
pub/sub channel and runs a background subscriber (one per uvicorn
worker) that fans messages out to the local in-memory
:class:`events.websocket.ConnectionManager`. It exists because the
manager keeps sockets per process, so with 2+ workers a direct
``manager.send_to_user`` call may land on a worker that does not hold
the recipient socket. Redis delivery is mandatory (no in-memory
fallback); bus errors never propagate and are only debug-logged.

Redis-шина событий для WebSocket-уведомлений между воркерами.

Модуль публикует конверты уведомлений в Redis pub/sub канал и держит
фонового подписчика (один на uvicorn-воркер), который разворачивает
сообщения в локальный in-memory
:class:`events.websocket.ConnectionManager`. Нужен, т.к. менеджер
хранит сокеты на процесс, и при 2+ воркерах прямой вызов
``manager.send_to_user`` может попасть не на тот процесс. Redis
обязателен (без fallback); ошибки шины наружу не бросаются,
только debug-лог.
"""

import asyncio
import json
import logging
from typing import Any
from uuid import UUID

import redis.asyncio as redis

from events.websocket import manager
from settings import cfg

CHANNEL: str = "events"

logger: logging.Logger = logging.getLogger(__name__)

_subscriber_task: asyncio.Task[None] | None = None
_subscriber_stop: asyncio.Event | None = None


def encode_event(recipients: list[UUID], payload: dict[str, Any]) -> str:
    """Serialize recipients and payload into a bus envelope JSON string.

    Сериализует получателей и payload в JSON-строку конверта шины.
    """
    return json.dumps(
        {
            "recipients": [str(user_id) for user_id in recipients],
            "payload": payload,
        }
    )


def decode_event(raw: str | bytes | None) -> tuple[list[UUID], dict[str, Any]]:
    """Parse a bus envelope back into recipients and payload.

    Разбирает конверт шины обратно в получателей и payload.

    Raises:
        ValueError: If the envelope is malformed.
    """
    if isinstance(raw, bytes):
        raw = raw.decode("utf-8")
    if not isinstance(raw, str):
        raise ValueError("empty event envelope")
    data: Any = json.loads(raw)
    if not isinstance(data, dict):
        raise ValueError("event envelope must be a JSON object")
    raw_recipients = data.get("recipients")
    payload = data.get("payload")
    if not isinstance(raw_recipients, list) or not isinstance(payload, dict):
        raise ValueError("event envelope must hold recipients list and payload dict")
    return [UUID(str(item)) for item in raw_recipients], payload


async def handle_message(data: str | bytes | None) -> None:
    """Deliver one raw bus message via the local connection manager.

    Доставляет одно сырое сообщение шины через локальный менеджер
    соединений. Никогда не бросает исключение наружу.
    """
    try:
        recipients, payload = decode_event(data)
    except Exception as exc:
        logger.debug("ignoring malformed event bus message: %s", exc)
        return
    for user_id in recipients:
        try:
            await manager.send_to_user(user_id, payload)
        except Exception as exc:
            logger.debug("local fan-out to %s failed: %s", user_id, exc)


async def publish_event(recipients: list[UUID], payload: dict[str, Any]) -> None:
    """Publish notification envelope to the Redis ``events`` channel.

    Публикует конверт уведомления в Redis-канал ``events``.
    Ошибка шины не бросает исключение наружу, только debug-лог.
    """
    try:
        raw = encode_event(recipients, payload)
        client = redis.from_url(cfg.REDIS_URL, decode_responses=True)
        try:
            await client.publish(CHANNEL, raw)
        finally:
            try:
                await client.aclose()
            except Exception as exc:
                logger.debug("closing redis publisher failed: %s", exc)
    except Exception as exc:
        logger.debug("event bus publish failed: %s", exc)


async def subscriber(stop: asyncio.Event | None = None) -> None:
    """Run the background Redis subscriber loop with reconnect backoff.

    Крутит фоновый цикл Redis-подписчика с переподключением и backoff.
    Читает канал, вызывает локальный ``manager.send_to_user`` для
    каждого получателя. При обрыве соединения переподключается
    с нарастающей паузой.
    """
    delay = 1.0
    while True:
        if stop is not None and stop.is_set():
            return
        client = None
        try:
            client = redis.from_url(cfg.REDIS_URL, decode_responses=True)
            pubsub = client.pubsub()
            await pubsub.subscribe(CHANNEL)
            delay = 1.0
            async for message in pubsub.listen():
                if stop is not None and stop.is_set():
                    return
                if not isinstance(message, dict) or message.get("type") != "message":
                    continue
                await handle_message(message.get("data"))
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            logger.debug("event bus subscriber error, reconnecting: %s", exc)
            if stop is not None and stop.is_set():
                return
            await asyncio.sleep(delay)
            delay = min(delay * 2.0, 30.0)
        finally:
            if client is not None:
                try:
                    await client.aclose()
                except Exception as exc:
                    logger.debug("closing redis subscriber failed: %s", exc)


async def start_subscriber() -> None:
    """Start the background subscriber task (one per worker, idempotent).

    Запускает фоновую задачу подписчика (одна на воркер, идемпотентно).
    """
    global _subscriber_task, _subscriber_stop
    if _subscriber_task is not None and not _subscriber_task.done():
        return
    _subscriber_stop = asyncio.Event()
    _subscriber_task = asyncio.create_task(subscriber(_subscriber_stop))


async def stop_subscriber() -> None:
    """Stop the background subscriber task (idempotent).

    Останавливает фоновую задачу подписчика (идемпотентно).
    """
    global _subscriber_task, _subscriber_stop
    task, _subscriber_task = _subscriber_task, None
    stop, _subscriber_stop = _subscriber_stop, None
    if stop is not None:
        stop.set()
    if task is not None:
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass
        except Exception as exc:
            logger.debug("subscriber shutdown error: %s", exc)

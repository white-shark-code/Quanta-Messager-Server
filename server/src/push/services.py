"""Services for Web Push subscriptions and delivery.

This module stores browser push subscriptions and delivers
ID-only notification payloads via ``pywebpush`` (best-effort:
delivery errors are only debug-logged and never fail the request).
Push payloads carry no names or ciphertext — only chat/message IDs —
because pushes travel through third-party servers (Google/Mozilla).
Stale endpoints reported by the push service (HTTP 410/404) are
removed from storage.

Сервисы подписок Web Push и доставки.

Модуль хранит браузерные пуш-подписки и доставляет payload
только с ID через ``pywebpush`` (best-effort: ошибки доставки
только debug-логгируются и никогда не роняют запрос). Пуш-payload
не содержит имён и шифротекста — только ID чата/сообщения, —
т.к. пуши идут через сторонние серверы (Google/Mozilla).
Протухшие endpoint, о которых сообщил пуш-сервис (HTTP 410/404),
удаляются из хранилища.
"""

import asyncio
import json
import logging
from typing import Any
from uuid import UUID

from pywebpush import WebPushException, webpush
from sqlalchemy import Select, select

from database import AsyncSession
from settings import cfg

from .models import PushSubscription

logger: logging.Logger = logging.getLogger(__name__)

PUSH_TTL_SECONDS: int = 2419200


def dialog_push_payload(chat_id: UUID, message_id: UUID) -> dict[str, Any]:
    """Build an ID-only push payload for a new dialog message.

    Формирует пуш-payload только с ID для нового сообщения в диалоге
    (без имён и шифротекста — решение по приватности).
    """
    return {
        "type": "new_dialog_message",
        "chat_id": str(chat_id),
        "message_id": str(message_id),
    }


def group_push_payload(chat_id: UUID, message_id: UUID) -> dict[str, Any]:
    """Build an ID-only push payload for a new group message.

    Формирует пуш-payload только с ID для нового сообщения в группе
    (без имён и шифротекста — решение по приватности).
    """
    return {
        "type": "new_group_message",
        "chat_id": str(chat_id),
        "message_id": str(message_id),
    }


async def upsert_subscription(
    session: AsyncSession,
    user_id: UUID,
    endpoint: str,
    p256dh: str,
    auth: str,
) -> tuple[PushSubscription, bool]:
    """Create or update a push subscription for the user.

    Создаёт или обновляет пуш-подписку пользователя.

    Args:
        session: Async database session.
        user_id: Owner of the subscription.
        endpoint: Push service endpoint URL (unique per subscription).
        p256dh: Browser public encryption key.
        auth: Browser auth secret.

    Returns:
        Tuple of the subscription and a flag (True if newly created).
    """
    stmt: Select = select(PushSubscription).where(
        PushSubscription.user_id == user_id,
        PushSubscription.endpoint == endpoint,
    )
    existing = (await session.execute(stmt)).scalar_one_or_none()
    if existing is None:
        subscription = PushSubscription(
            user_id=user_id, endpoint=endpoint, p256dh=p256dh, auth=auth
        )
        session.add(subscription)
        return subscription, True
    existing.p256dh = p256dh
    existing.auth = auth
    return existing, False


async def delete_subscription(
    session: AsyncSession, user_id: UUID, endpoint: str
) -> bool:
    """Delete the user's own push subscription (idempotent).

    Удаляет собственную пуш-подписку пользователя (идемпотентно).

    Args:
        session: Async database session.
        user_id: Owner whose subscription may be deleted.
        endpoint: Push service endpoint URL to delete.

    Returns:
        True if a subscription was deleted, False if there was none.
    """
    stmt: Select = select(PushSubscription).where(
        PushSubscription.user_id == user_id,
        PushSubscription.endpoint == endpoint,
    )
    existing = (await session.execute(stmt)).scalar_one_or_none()
    if existing is None:
        return False
    await session.delete(existing)
    return True


async def delete_subscription_by_endpoint(
    session: AsyncSession, endpoint: str
) -> bool:
    """Delete a push subscription by endpoint regardless of owner.

    Удаляет пуш-подписку по endpoint вне зависимости от владельца.
    Используется для чистки протухших endpoint по ответу пуш-сервиса.

    Args:
        session: Async database session.
        endpoint: Push service endpoint URL to delete.

    Returns:
        True if a subscription was deleted, False if there was none.
    """
    stmt: Select = select(PushSubscription).where(
        PushSubscription.endpoint == endpoint
    )
    existing = (await session.execute(stmt)).scalar_one_or_none()
    if existing is None:
        return False
    await session.delete(existing)
    return True


async def get_subscriptions_for_users(
    session: AsyncSession, user_ids: list[UUID]
) -> list[PushSubscription]:
    """Return all push subscriptions of the given users.

    Возвращает все пуш-подписки указанных пользователей.

    Args:
        session: Async database session.
        user_ids: Subscription owners to look up.

    Returns:
        List of stored push subscriptions (may be empty).
    """
    stmt: Select = select(PushSubscription).where(
        PushSubscription.user_id.in_(user_ids)
    )
    return list((await session.execute(stmt)).scalars().all())


def _deliver(subscription_info: dict[str, Any], data: str) -> None:
    """Send one push message via pywebpush (blocking, run in a thread).

    Отправляет одно пуш-сообщение через pywebpush (блокирующий вызов,
    выполнять в отдельном потоке).
    """
    webpush(
        subscription_info=subscription_info,
        data=data,
        vapid_private_key=cfg.VAPID_PRIVATE_KEY,
        vapid_claims={"sub": cfg.VAPID_CLAIMS_SUB},
        ttl=PUSH_TTL_SECONDS,
        headers={"Urgency": "normal"},
    )


async def send_push_to_users(
    session: AsyncSession, user_ids: list[UUID], payload: dict[str, Any]
) -> None:
    """Deliver a Web Push payload to users' browsers (best-effort).

    Доставляет Web Push-payload в браузеры пользователей (best-effort).

    Looks up stored subscriptions, sends one encrypted push per
    subscription in a worker thread, and removes endpoints the push
    service reports as gone (HTTP 410/404). Never raises: every
    failure is only debug-logged. Skips silently when VAPID settings
    are not configured.
    """
    if not user_ids:
        return
    if not cfg.VAPID_PRIVATE_KEY or not cfg.VAPID_CLAIMS_SUB:
        logger.debug("web push skipped: VAPID not configured")
        return
    try:
        subscriptions = await get_subscriptions_for_users(session, user_ids)
    except Exception as exc:
        logger.debug("web push subscriptions lookup failed: %s", exc)
        return
    data = json.dumps(payload, separators=(",", ":"))
    for subscription in subscriptions:
        subscription_info = {
            "endpoint": subscription.endpoint,
            "keys": {"p256dh": subscription.p256dh, "auth": subscription.auth},
        }
        try:
            await asyncio.to_thread(_deliver, subscription_info, data)
        except WebPushException as exc:
            if exc.status_code in (404, 410):
                try:
                    await delete_subscription_by_endpoint(
                        session, subscription.endpoint
                    )
                    await session.commit()
                except Exception as cleanup_exc:
                    logger.debug(
                        "web push stale endpoint cleanup failed: %s", cleanup_exc
                    )
            else:
                logger.debug("web push delivery failed: %s", exc)
        except Exception as exc:
            logger.debug("web push delivery failed: %s", exc)

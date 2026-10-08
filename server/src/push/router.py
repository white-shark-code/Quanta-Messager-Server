"""Push API router for Web Push subscription management.

This module provides REST endpoints for subscribing browsers to,
and unsubscribing them from, Web Push notifications. Both endpoints
require authentication; users can only manage their own subscriptions.

Роутер API пушей для управления подписками Web Push.

Модуль предоставляет REST-эндпоинты для подписки браузеров на
Web Push-уведомления и отписки от них. Оба эндпоинта требуют
аутентификации; пользователь управляет только своими подписками.
"""

from fastapi import APIRouter, Depends, Response, status

from authentication.models import User
from authentication.services import current_user_av
from database import AsyncSession, get_async_session

from .schemas import (
    PushSubscribeRequest,
    PushSubscriptionResponse,
    PushUnsubscribeRequest,
)
from .services import delete_subscription, upsert_subscription

push: APIRouter = APIRouter(prefix="/push")


@push.post(path="/subscribe", response_model=PushSubscriptionResponse)
async def subscribe_push(
    data: PushSubscribeRequest,
    response: Response,
    user: User = Depends(dependency=current_user_av),
    session: AsyncSession = Depends(dependency=get_async_session),
):
    """Subscribe the browser to Web Push notifications (upsert).

    Подписывает браузер на Web Push-уведомления (upsert).

    Creates a new subscription (HTTP 201) or refreshes the keys of an
    existing one for the same endpoint (HTTP 200).
    """
    subscription, created = await upsert_subscription(
        session,
        user_id=user.id,
        endpoint=data.endpoint,
        p256dh=data.keys.p256dh,
        auth=data.keys.auth,
    )
    await session.commit()
    response.status_code = (
        status.HTTP_201_CREATED if created else status.HTTP_200_OK
    )
    return PushSubscriptionResponse(endpoint=subscription.endpoint)


@push.delete(path="/unsubscribe", status_code=status.HTTP_204_NO_CONTENT)
async def unsubscribe_push(
    data: PushUnsubscribeRequest,
    user: User = Depends(dependency=current_user_av),
    session: AsyncSession = Depends(dependency=get_async_session),
):
    """Remove a browser push subscription (idempotent).

    Удаляет пуш-подписку браузера (идемпотентно).

    Always returns HTTP 204, even if the endpoint was not subscribed.
    Only the current user's own subscription can be removed.
    """
    await delete_subscription(session, user_id=user.id, endpoint=data.endpoint)
    await session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)

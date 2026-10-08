"""Push schemas for Web Push subscription API validation.

This module defines Pydantic schemas for subscribing and
unsubscribing browsers to Web Push notifications.

Схемы пушей для валидации API подписок Web Push.

Модуль определяет Pydantic-схемы для подписки и отписки браузеров
на Web Push-уведомления.
"""

from pydantic import BaseModel, ConfigDict


class PushKeys(BaseModel):
    """Browser-generated encryption keys of a push subscription.

    Сгенерированные браузером ключи шифрования пуш-подписки.
    """

    p256dh: str
    auth: str


class PushSubscribeRequest(BaseModel):
    """Request body for subscribing the browser to push notifications.

    Тело запроса для подписки браузера на пуш-уведомления.
    """

    endpoint: str
    keys: PushKeys


class PushUnsubscribeRequest(BaseModel):
    """Request body for removing a browser push subscription.

    Тело запроса для удаления пуш-подписки браузера.
    """

    endpoint: str


class PushSubscriptionResponse(BaseModel):
    """Response body for push subscribe endpoints.

    Тело ответа эндпоинтов подписки на пуши.
    """

    model_config = ConfigDict(from_attributes=True)

    endpoint: str

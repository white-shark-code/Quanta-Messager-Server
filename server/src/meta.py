"""Server metadata endpoint (VAPID public key for Web Push).

This module exposes public runtime metadata the frontend needs
before subscribing to push notifications — currently the VAPID
public key used to subscribe the Service Worker. No secrets are
ever returned here; authentication is not required.

Эндпоинт метаданных сервера (VAPID-публичный ключ для Web Push).

Модуль отдаёт публичные метаданные, нужные фронтенду до подписки
на пуш-уведомления, — сейчас это VAPID-публичный ключ для подписки
Service Worker. Секреты здесь никогда не возвращаются;
аутентификация не требуется.
"""

from fastapi import APIRouter

from settings import cfg

meta: APIRouter = APIRouter()


@meta.get(path="/meta")
async def get_meta() -> dict[str, str]:
    """Return public server metadata for frontend bootstrap.

    Возвращает публичные метаданные сервера для инициализации фронтенда.

    Returns:
        Mapping with the VAPID public key (empty string if not configured).
    """
    return {"vapid_public_key": cfg.VAPID_PUBLIC_KEY}

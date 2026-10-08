"""Push subscription models for Web Push notifications.

This module defines the SQLAlchemy ORM model that stores browser
push subscription credentials (endpoint + encryption keys) per user.
One browser endpoint is globally unique: a subscription always
belongs to exactly one user.

Модели подписок для Web Push-уведомлений.

Модуль определяет SQLAlchemy ORM-модель, хранящую учётные данные
браузерных пуш-подписок (endpoint + ключи шифрования) на пользователя.
Endpoint глобально уникален: подписка всегда принадлежит ровно
одному пользователю.
"""

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column

from authentication.models import User
from shared.abstract_sqlalchemy_models import AbstractModelWithUUID


class PushSubscription(AbstractModelWithUUID):
    """Browser push subscription of a user.

    Подписка браузера пользователя на пуш-уведомления.
    """

    __tablename__: str = "push_subscriptions"

    user_id: Mapped[UUID] = mapped_column(
        ForeignKey(column=User.id, ondelete="CASCADE"), nullable=False
    )
    endpoint: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    p256dh: Mapped[str] = mapped_column(Text, nullable=False)
    auth: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(UTC).replace(tzinfo=None),
        nullable=False,
    )

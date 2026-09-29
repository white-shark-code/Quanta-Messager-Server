"""Database models for messaging system.

Модели базы данных для системы сообщений.
"""

from datetime import datetime, timezone
from uuid import UUID, uuid4

from fastapi_users_db_sqlalchemy.generics import GUID
from sqlalchemy import ForeignKey, LargeBinary, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from authentication.models import User
from shared.abstract_sqlalchemy_models import (
    AbstractModel,
    AbstractModelWithCreateAt,
    AbstractModelWithUUID,
)


class BasicChat(AbstractModelWithUUID, AbstractModelWithCreateAt):
    """Abstract base class for all chat models.

    Абстрактный базовый класс для всех моделей чатов.
    """

    __abstract__: bool = True

    name: Mapped[str]


class DialogChat(BasicChat):
    """Database model for dialog chats between two users.

    Модель базы данных для диалогов между двумя пользователями.
    """

    __tablename__: str = "dialog_chats"

    user0: Mapped[UUID] = mapped_column(
        ForeignKey(column=User.id, ondelete="CASCADE"), nullable=False
    )
    user1: Mapped[UUID] = mapped_column(
        ForeignKey(column=User.id, ondelete="CASCADE"), nullable=False
    )


class GroupChat(BasicChat):
    """Database model for group chats with multiple users.

    Модель базы данных для групповых чатов с несколькими пользователями.
    """

    __tablename__: str = "group_chats"

    users: Mapped[UUID] = relationship(
        argument="User", secondary="user_groups", back_populates="groups"
    )
    public_key: Mapped[bytes] = mapped_column(nullable=False)


class BasicMessage(AbstractModelWithUUID, AbstractModelWithCreateAt):
    """Abstract base class for all message models.

    Абстрактный базовый класс для моделей сообщений.
    """

    __abstract__: bool = True

    id: Mapped[UUID] = mapped_column(GUID, primary_key=True, default=uuid4)
    owner_id: Mapped[UUID] = mapped_column(ForeignKey(column=User.id), nullable=False)
    encrypted_message: Mapped[bytes] = mapped_column(nullable=False)
    # Detached PGP signature over the *ciphertext* (see
    # `services.chech_signature_and_encryption`). Nullable so the
    # migration doesn't break pre-existing rows that were written
    # before this column existed.
    signature: Mapped[bytes | None] = mapped_column(LargeBinary, nullable=True)
    # Sender's own copy of the same plaintext, encrypted to the
    # sender's key (see `services.chech_signature_and_encryption`
    # applied to the pair as well). Lets the sender (and all of
    # their devices sharing the keypair) decrypt what they sent —
    # the main `encrypted_message` is readable only by the peer.
    # NOT NULL: there is no production yet, old rows are dropped
    # instead of migrated.
    encrypted_message_self: Mapped[bytes] = mapped_column(
        LargeBinary, nullable=False
    )
    # Detached PGP signature over `encrypted_message_self`,
    # verified against the sender's stored public key on every send.
    signature_self: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    creation_datetime: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(timezone.utc).replace(tzinfo=None),
        nullable=False,
    )


class DialogMessage(BasicMessage):
    """Database model for messages in dialog chats.

    Модель базы данных для сообщений в диалоговых чатах.
    """

    __tablename__: str = "dialog_messages"

    chat_id: Mapped[UUID] = mapped_column(
        ForeignKey(column=DialogChat.id, ondelete="CASCADE")
    )


class GroupMessage(BasicMessage):
    """Database model for messages in group chats.

    Модель базы данных для сообщений в групповых чатах.
    """

    __tablename__: str = "group_messages"

    chat_id: Mapped[UUID] = mapped_column(
        ForeignKey(column=GroupChat.id, ondelete="CASCADE")
    )


class MediaAttachment(AbstractModelWithUUID):
    """Database model for media attachment metadata.

    Модель базы данных для метаданных медиа-вложений.
    """

    __tablename__: str = "media_attachments"

    dialog_message_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("dialog_messages.id"), nullable=True, default=None
    )
    group_message_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("group_messages.id"), nullable=True, default=None
    )
    mime_type: Mapped[str] = mapped_column(String(128), nullable=False)
    file_size: Mapped[int] = mapped_column(nullable=False)
    signature: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    creation_datetime: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(timezone.utc).replace(tzinfo=None),
        nullable=False,
    )
    owner_id: Mapped[UUID] = mapped_column(ForeignKey(column=User.id), nullable=False)


class MediaBlobData(AbstractModel):
    """Database model for encrypted media blob storage.

    Модель базы данных для хранения зашифрованных медиа-блобов.
    """

    __tablename__: str = "media_blob_data"

    media_id: Mapped[UUID] = mapped_column(
        GUID,
        ForeignKey(column=MediaAttachment.id, ondelete="CASCADE"),
        primary_key=True,
    )
    encrypted_file: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)

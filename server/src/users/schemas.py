"""Schemas for user-lookup endpoints.

Схемы для эндпоинтов поиска пользователей.
"""
from uuid import UUID

from pydantic import BaseModel


class PublicKeyResponse(BaseModel):
    """Response schema for the per-user public-key lookup endpoint.

    The frontend uses this to decide whether a peer can receive
    end-to-end encrypted messages: if ``has_public_key`` is False
    the UI disables the composer for that chat and shows a banner
    explaining the peer hasn't set up PGP yet.

    ``public_key`` mirrors the storage shape used elsewhere in the
    API (``bytes | None``); FastAPI base64-encodes raw ``bytes``
    on the wire via its JSON encoder, matching how
    ``UserReadWithPGP.public_key`` is already serialized.
    """

    user_id: UUID
    has_public_key: bool
    public_key: bytes | None = None

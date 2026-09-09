import base64
from typing import Any
from uuid import UUID

from httpx import Response

from .services import BasicAPI, client, pgp_sign


def _b64(data: bytes) -> str:
    """Base64-encode raw bytes for JSON serialization to a Base64Bytes field."""
    return base64.b64encode(data).decode("ascii")


class MessageAPI(BasicAPI):
    @staticmethod
    async def get_private_chats(
        auth: dict[str, str],
        last_id: UUID | None = None,
        page_size: int = 10,
    ) -> dict[str, Any]:
        qs = f"last_id={last_id}&page_size={page_size}" if last_id else f"page_size={page_size}"
        response: Response = await client.get(
            headers=auth, url=f"/messages/private-chats/?{qs}"
        )

        assert response.status_code == 200

        return response.json()

    @staticmethod
    async def get_private_chat_by_id(auth: dict[str, str], id: UUID) -> dict[str, Any]:
        response: Response = await client.get(
            headers=auth, url=f"/messages/private-chat/{id}"
        )

        assert response.status_code == 200

        return response.json()

    @staticmethod
    async def post_private_chat(
        auth: dict[str, str], user_id: UUID, chat_name: str
    ) -> dict[str, Any]:
        response: Response = await client.post(
            headers=auth,
            url="/messages/private-chat/",
            json={"name": chat_name, "user": str(user_id)},
        )

        assert response.status_code == 200

        return response.json()

    @staticmethod
    async def delete_private_chat_by_id(
        auth: dict[str, str], chat_id: UUID
    ) -> dict[str, Any]:
        response: Response = await client.delete(
            headers=auth, url=f"/messages/private-chat/{chat_id}/"
        )

        assert response.status_code == 200

        return response.json()

    @staticmethod
    async def get_private_messages(
        auth: dict[str, str], chat_id: UUID, page: int = 1, count: int = 10
    ) -> dict[str, Any]:
        response: Response = await client.get(
            headers=auth,
            url=f"/messages/private-messages/{chat_id}?page={page}&count={count}",
        )

        assert response.status_code == 200

        return response.json()

    @staticmethod
    async def post_private_message(
        auth: dict[str, str],
        chat_id: UUID,
        sender_user: str,
        recipient_user: str,
        message: str,
    ) -> dict[str, Any]:
        """Encrypt + sign + send a private message via the API.

        ``sender_user`` / ``recipient_user`` are the test user handles
        (e.g. ``"user0"``, ``"user1"``) whose GnuPG keys were generated
        by the session fixture.
        """
        from .services import pgp_encrypt

        plaintext = message.encode("utf-8")
        encrypted: bytes = pgp_encrypt(
            sender_user, recipient_user, plaintext
        )
        signature: bytes = pgp_sign(sender_user, encrypted)

        response: Response = await client.post(
            headers=auth,
            url=f"/messages/private-message/{chat_id}",
            json={
                "encrypted_message": _b64(encrypted),
                "signature": _b64(signature),
            },
        )

        assert response.status_code == 200

        return response.json()

    @staticmethod
    async def get_group_chats(
        auth: dict[str, str],
        last_id: UUID | None = None,
        page_size: int = 10,
    ) -> dict[str, Any]:
        qs = f"last_id={last_id}&page_size={page_size}" if last_id else f"page_size={page_size}"
        response: Response = await client.get(
            headers=auth, url=f"/group-messages/group-chats/?{qs}"
        )

        assert response.status_code == 200

        return response.json()

    @staticmethod
    async def get_group_chat_by_id(auth: dict[str, str], id: UUID) -> dict[str, Any]:
        response: Response = await client.get(
            headers=auth, url=f"/group-messages/group-chat/{id}"
        )

        assert response.status_code == 200

        return response.json()

    @staticmethod
    async def post_group_chat(
        auth: dict[str, str],
        chat_name: str,
        public_key: bytes = b"placeholder-pgp-public-key",
    ) -> dict[str, Any]:
        response: Response = await client.post(
            headers=auth,
            url="/group-messages/group-chat/",
            json={"name": chat_name, "public_key": public_key.decode("utf-8")},
        )

        assert response.status_code == 200

        return response.json()

    @staticmethod
    async def delete_group_chat_by_id(
        auth: dict[str, str], chat_id: UUID
    ) -> dict[str, Any]:
        response: Response = await client.delete(
            headers=auth, url=f"/group-messages/group-chat/{chat_id}/"
        )

        assert response.status_code == 200

        return response.json()

    @staticmethod
    async def get_group_messages(
        auth: dict[str, str], chat_id: UUID, page: int = 1, count: int = 10
    ) -> dict[str, Any]:
        response: Response = await client.get(
            headers=auth,
            url=f"/group-messages/group-messages/{chat_id}?page={page}&count={count}",
        )

        assert response.status_code == 200

        return response.json()

    @staticmethod
    async def post_group_message(
        auth: dict[str, str],
        chat_id: UUID,
        sender_user: str,
        recipient_user: str,
        message: str,
    ) -> dict[str, Any]:
        """Encrypt + sign + send a group message via the API."""
        from .services import pgp_encrypt

        plaintext = message.encode("utf-8")
        encrypted: bytes = pgp_encrypt(
            sender_user, recipient_user, plaintext
        )
        signature: bytes = pgp_sign(sender_user, encrypted)

        response: Response = await client.post(
            headers=auth,
            url=f"/group-messages/group-message/{chat_id}",
            json={
                "encrypted_message": _b64(encrypted),
                "signature": _b64(signature),
            },
        )

        assert response.status_code == 200

        return response.json()

    @staticmethod
    async def upload_private_media(
        auth: dict[str, str],
        chat_id: UUID,
        sender_user: str,
        encrypted_file: bytes,
    ) -> dict[str, Any]:
        """Upload media: sign the encrypted_file with sender's private key."""
        signature: bytes = pgp_sign(sender_user, encrypted_file)

        response: Response = await client.post(
            headers=auth,
            url=f"/messages/private-message/{chat_id}/media/upload",
            json={
                "encrypted_file": _b64(encrypted_file),
                "signature": _b64(signature),
                "mime_type": "text/plain",
                "file_size": len(encrypted_file),
            },
        )

        assert response.status_code == 201

        return response.json()

    @staticmethod
    async def list_private_media(
        auth: dict[str, str],
        message_id: UUID,
    ) -> dict[str, Any]:
        response: Response = await client.get(
            headers=auth,
            url=f"/messages/private-message/{message_id}/media/",
        )

        assert response.status_code == 200

        return response.json()

    @staticmethod
    async def download_private_media(
        auth: dict[str, str],
        media_id: UUID,
    ) -> dict[str, Any]:
        response: Response = await client.get(
            headers=auth,
            url=f"/messages/private-message/media/{media_id}",
        )

        assert response.status_code == 200

        return response.json()

    @staticmethod
    async def delete_private_media(
        auth: dict[str, str],
        media_id: UUID,
    ) -> dict[str, Any]:
        response: Response = await client.delete(
            headers=auth,
            url=f"/messages/private-message/media/{media_id}/",
        )

        assert response.status_code == 200

        return response.json()

    @staticmethod
    async def upload_group_media(
        auth: dict[str, str],
        chat_id: UUID,
        sender_user: str,
        encrypted_file: bytes,
    ) -> dict[str, Any]:
        signature: bytes = pgp_sign(sender_user, encrypted_file)

        response: Response = await client.post(
            headers=auth,
            url=f"/group-messages/group-message/{chat_id}/media/upload",
            json={
                "encrypted_file": _b64(encrypted_file),
                "signature": _b64(signature),
                "mime_type": "text/plain",
                "file_size": len(encrypted_file),
            },
        )

        assert response.status_code == 201

        return response.json()

    @staticmethod
    async def list_group_media(
        auth: dict[str, str],
        message_id: UUID,
    ) -> dict[str, Any]:
        response: Response = await client.get(
            headers=auth,
            url=f"/group-messages/group-message/{message_id}/media/",
        )

        assert response.status_code == 200

        return response.json()

    @staticmethod
    async def download_group_media(
        auth: dict[str, str],
        media_id: UUID,
    ) -> dict[str, Any]:
        response: Response = await client.get(
            headers=auth,
            url=f"/group-messages/group-message/media/{media_id}",
        )

        assert response.status_code == 200

        return response.json()

    @staticmethod
    async def delete_group_media(
        auth: dict[str, str],
        media_id: UUID,
    ) -> dict[str, Any]:
        response: Response = await client.delete(
            headers=auth,
            url=f"/group-messages/group-message/media/{media_id}/",
        )

        assert response.status_code == 200

        return response.json()

    @staticmethod
    async def post_private_message_with_media(
        auth: dict[str, str],
        chat_id: UUID,
        sender_user: str,
        recipient_user: str,
        message: str,
        media_ids: list[UUID],
    ) -> dict[str, Any]:
        from .services import pgp_encrypt

        plaintext = message.encode("utf-8")
        encrypted: bytes = pgp_encrypt(
            sender_user, recipient_user, plaintext
        )
        signature: bytes = pgp_sign(sender_user, encrypted)

        response: Response = await client.post(
            headers=auth,
            url=f"/messages/private-message/{chat_id}",
            json={
                "encrypted_message": _b64(encrypted),
                "signature": _b64(signature),
                "media_ids": [str(mid) for mid in media_ids],
            },
        )

        assert response.status_code == 200

        return response.json()

    @staticmethod
    async def post_group_message_with_media(
        auth: dict[str, str],
        chat_id: UUID,
        sender_user: str,
        recipient_user: str,
        message: str,
        media_ids: list[UUID],
    ) -> dict[str, Any]:
        from .services import pgp_encrypt

        plaintext = message.encode("utf-8")
        encrypted: bytes = pgp_encrypt(
            sender_user, recipient_user, plaintext
        )
        signature: bytes = pgp_sign(sender_user, encrypted)

        response: Response = await client.post(
            headers=auth,
            url=f"/group-messages/group-message/{chat_id}",
            json={
                "encrypted_message": _b64(encrypted),
                "signature": _b64(signature),
                "media_ids": [str(mid) for mid in media_ids],
            },
        )

        assert response.status_code == 200

        return response.json()

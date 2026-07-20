from typing import Any
from uuid import UUID

from httpx import Response
from pgpy import PGPKey, PGPMessage, PGPSignature

from .services import BasicAPI, client


class MessageAPI(BasicAPI):
    @staticmethod
    async def get_private_chats(
        auth: dict[str, str], page: int = 1, count: int = 10
    ) -> dict[str, Any]:
        response: Response = await client.get(
            headers=auth, url=f"/messages/private-chats/?page={page}&count={count}"
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
            json={"name": chat_name, "user": user_id},
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
        public_key: PGPKey,
        private_key: PGPKey,
        message: str,
    ) -> dict[str, Any]:
        message: PGPMessage = PGPMessage.new(message=message)

        encrypted_message: PGPMessage = public_key.encrypt(message=message)

        signature: PGPSignature = private_key.sign(subject=bytes(encrypted_message))

        response: Response = await client.post(
            headers=auth,
            url=f"/messages/private-message/{chat_id}",
            json={
                "encrypted_message": str(encrypted_message),
                "signature": str(signature),
            },
        )

        assert response.status_code == 200

        return response.json()

    @staticmethod
    async def get_group_chats(
        auth: dict[str, str], page: int = 1, count: int = 10
    ) -> dict[str, Any]:
        response: Response = await client.get(
            headers=auth, url=f"/group-messages/group-chats/?page={page}&count={count}"
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
    async def post_group_chat(auth: dict[str, str], chat_name: str) -> dict[str, Any]:
        response: Response = await client.post(
            headers=auth, url="/group-messages/group-chat/", json={"name": chat_name}
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
        public_key: PGPKey,
        private_key: PGPKey,
        message: str,
    ) -> dict[str, Any]:
        message: PGPMessage = PGPMessage.new(message=message)

        encrypted_message: PGPMessage = public_key.encrypt(message=message)

        signature: PGPSignature = private_key.sign(subject=bytes(encrypted_message))

        response: Response = await client.post(
            headers=auth,
            url=f"/group-messages/group-message/{chat_id}",
            json={
                "encrypted_message": str(encrypted_message),
                "signature": str(signature),
            },
        )

        assert response.status_code == 200

        return response.json()

    @staticmethod
    async def upload_private_media(
        auth: dict[str, str],
        chat_id: UUID,
        encrypted_file: bytes,
        signature: bytes,
        mime_type: str,
        file_size: int,
    ) -> dict[str, Any]:
        response: Response = await client.post(
            headers=auth,
            url=f"/messages/private-message/{chat_id}/media/upload",
            json={
                "encrypted_file": encrypted_file.decode("utf-8"),
                "signature": signature.decode("utf-8"),
                "mime_type": mime_type,
                "file_size": file_size,
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
        encrypted_file: bytes,
        signature: bytes,
        mime_type: str,
        file_size: int,
    ) -> dict[str, Any]:
        response: Response = await client.post(
            headers=auth,
            url=f"/group-messages/group-message/{chat_id}/media/upload",
            json={
                "encrypted_file": encrypted_file.decode("utf-8"),
                "signature": signature.decode("utf-8"),
                "mime_type": mime_type,
                "file_size": file_size,
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
        public_key: PGPKey,
        private_key: PGPKey,
        message: str,
        media_ids: list[UUID],
    ) -> dict[str, Any]:
        msg: PGPMessage = PGPMessage.new(message=message)

        encrypted_message: PGPMessage = public_key.encrypt(message=msg)

        signature: PGPSignature = private_key.sign(subject=bytes(encrypted_message))

        response: Response = await client.post(
            headers=auth,
            url=f"/messages/private-message/{chat_id}",
            json={
                "encrypted_message": str(encrypted_message),
                "signature": str(signature),
                "media_ids": [str(mid) for mid in media_ids],
            },
        )

        assert response.status_code == 200

        return response.json()

    @staticmethod
    async def post_group_message_with_media(
        auth: dict[str, str],
        chat_id: UUID,
        public_key: PGPKey,
        private_key: PGPKey,
        message: str,
        media_ids: list[UUID],
    ) -> dict[str, Any]:
        msg: PGPMessage = PGPMessage.new(message=message)

        encrypted_message: PGPMessage = public_key.encrypt(message=msg)

        signature: PGPSignature = private_key.sign(subject=bytes(encrypted_message))

        response: Response = await client.post(
            headers=auth,
            url=f"/group-messages/group-message/{chat_id}",
            json={
                "encrypted_message": str(encrypted_message),
                "signature": str(signature),
                "media_ids": [str(mid) for mid in media_ids],
            },
        )

        assert response.status_code == 200

        return response.json()

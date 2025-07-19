from uuid import UUID

from httpx import Response
from pgpy import PGPKey, PGPMessage, PGPSignature

from .services import BasicAPI, client


class MessageAPI(BasicAPI):
    @staticmethod
    def get_private_chats(
        auth: dict[str, str],
        page: int = 1,
        count: int = 10
    ):
        response: Response = client.get(
            headers=auth,
            url=f'/messages/private-chats/?page={page}&count={count}'
        )

        assert response.status_code == 200

        return response.json()

    @staticmethod
    def get_private_chat_by_id(
        auth: dict[str, str],
        id: UUID
    ):
        response: Response = client.get(
            headers=auth,
            url=f'/messages/private-chat/{id}'
        )

        assert response.status_code == 200

        return response.json()

    @staticmethod
    def post_private_chat(
        auth: dict[str, str],
        user_id: UUID,
        chat_name: str
    ):
        response: Response = client.post(
            headers=auth,
            url='/messages/private-chat',
            json={
                'name': chat_name,
                'user': user_id
            }
        )

        assert response.status_code == 200

        return response.json()

    @staticmethod
    def delete_private_chat_by_id(
        auth: dict[str, str],
        chat_id: UUID
    ):
        response: Response = client.delete(
            headers=auth,
            url=f'/messages/private-chat/{chat_id}/'
        )

        assert response.status_code == 200

        return response.json()

    @staticmethod
    def get_private_messages(
        auth: dict[str, str],
        chat_id: UUID,
        page: int = 1,
        count: int = 10
    ):
        response: Response = client.get(
            headers=auth,
            url=f'/messages/private-messages/{chat_id}?page={page}&count={count}'
        )

        assert response.status_code == 200

        return response.json()

    @staticmethod
    def post_private_message(
        auth: dict[str, str],
        chat_id: UUID,
        public_key: PGPKey,
        private_key: PGPKey,
        message: str
    ):
        message: PGPMessage = PGPMessage.new(message=message)

        encrypted_message: PGPMessage = public_key.encrypt(message=message)

        signature: PGPSignature = private_key.sign(subject=bytes(encrypted_message))

        response: Response = client.post(
            headers=auth,
            url=f'/messages/private-message/{chat_id}',
            json={
                'encrypted_message': str(encrypted_message),
                'signature': str(signature)
            }
        )

        assert response.status_code == 200

        return response.json()

from typing import Any

from pgpy import PGPKey
from pytest import mark

from ..events_api import EventsAPI
from ..messages_api import MessageAPI
from ..services import generate_login_headers, get_me, login_post


@mark.usefixtures('create_users')
class TestMessagesAPI:
    def test_check_chat_diff_users(self, users: list[dict[str, str]]):

        response_login_user0: dict[str, Any] = login_post(
            email=users[0]['email'],
            password=users[0]['password']
        )

        response_login_user1: dict[str, Any] = login_post(
            email=users[1]['email'],
            password=users[1]['password']
        )

        user0_auth: dict[str, str] = generate_login_headers(
            login_answer = response_login_user0
        )
        user1_auth: dict[str, str] = generate_login_headers(
            login_answer = response_login_user1
        )

        response_me_user0: dict[str, Any] = get_me(auth=user0_auth)

        response_new_chat: dict[str, Any] = MessageAPI.post_private_chat(
            auth=user1_auth,
            user_id=response_me_user0['id'],
            chat_name='Test'
        )

        assert response_new_chat['name'] == 'Test'

        response_delete_chat: dict[str, Any] = MessageAPI.delete_private_chat_by_id(
            auth=user0_auth,
            chat_id=response_new_chat['id'],
        )

        assert response_delete_chat['id'] == response_new_chat['id']

    def test_create_and_delete_chat(self, login: dict[str, str]):
        response_me_user: dict[str, Any] = get_me(auth=login)

        response_new_chat: dict[str, Any] = MessageAPI.post_private_chat(
            auth=login,
            user_id=response_me_user['id'],
            chat_name='Test'
        )

        assert response_new_chat['name'] == 'Test'

        response_delete_chat: dict[str, Any] = MessageAPI.delete_private_chat_by_id(
            auth=login,
            chat_id=response_new_chat['id'],
        )

        assert response_delete_chat['id'] == response_new_chat['id']

    def test_sending_encrypted_text(
        self,
        users: list[dict[str, str]],
        gpg_keys: dict[str, dict[str, PGPKey]]
    ):
        response_login_user0: dict[str, Any] = login_post(
            email=users[0]['email'],
            password=users[0]['password']
        )

        response_login_user1: dict[str, Any] = login_post(
            email=users[1]['email'],
            password=users[1]['password']
        )

        user0_auth: dict[str, str] = generate_login_headers(
            login_answer = response_login_user0
        )
        user1_auth: dict[str, str] = generate_login_headers(
            login_answer = response_login_user1
        )

        response_me_user1: dict[str, Any] = get_me(auth=user1_auth)

        response_new_chat: dict[str, Any] = MessageAPI.post_private_chat(
            auth=user0_auth,
            user_id=response_me_user1['id'],
            chat_name='Test'
        )

        assert response_new_chat['name'] == 'Test'

        response_new_message: dict[str, Any] = MessageAPI.post_private_message(
            auth = user0_auth,
            chat_id = response_new_chat['id'],
            private_key = gpg_keys[users[0]['email']]['private'],
            public_key = gpg_keys[users[1]['email']]['public'],
            message='Test'
        )

        response_get_events_0: dict[str, Any] = EventsAPI.get_events_private_chats(
            auth = user1_auth
        )

        assert response_get_events_0['items'][0]['count'] == 1

        EventsAPI.mark_readed_private_chat(
            auth = user1_auth,
            event_id = response_get_events_0['items'][0]['id']
        )

        response_get_events_1: dict[str, Any] = EventsAPI.get_events_private_chats(
            auth = user1_auth
        )

        assert response_get_events_1['items'][0]['count'] == 0

        response_get_message_user1: dict[str, Any] = MessageAPI.get_private_messages(
            auth = user1_auth,
            chat_id = response_new_chat['id']
        )

        encrypted_message_json: dict[str, Any] = response_get_message_user1['items'][0]

        assert response_new_message['encrypted_message'] \
            == encrypted_message_json['encrypted_message']

        assert response_new_message['id'] == encrypted_message_json['id']

        assert response_new_message['owner_id'] == encrypted_message_json['owner_id']

        assert response_new_message['creation_datetime'] \
            == encrypted_message_json['creation_datetime']

        assert response_new_message['chat_id'] == encrypted_message_json['chat_id']

        response_delete_chat: dict[str, Any] = MessageAPI.delete_private_chat_by_id(
            auth=user1_auth,
            chat_id=response_new_chat['id'],
        )

        assert response_delete_chat['id'] == response_new_chat['id']

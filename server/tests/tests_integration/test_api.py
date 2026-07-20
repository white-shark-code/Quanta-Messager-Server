from typing import Any

from httpx import Response as HttpxResponse
from pgpy import PGPKey

from ..events_api import EventsAPI
from ..messages_api import MessageAPI
from ..services import (
    client,
    create_user_post,
    generate_login_headers,
    get_me,
    login_post,
)


class TestMessagesAPI:
    async def test_check_chat_diff_users(self, users: list[dict[str, str]]):
        response_login_user0: dict[str, Any] = await login_post(
            email=users[0]["email"], password=users[0]["password"]
        )

        response_login_user1: dict[str, Any] = await login_post(
            email=users[1]["email"], password=users[1]["password"]
        )

        user0_auth: dict[str, str] = generate_login_headers(
            login_answer=response_login_user0
        )
        user1_auth: dict[str, str] = generate_login_headers(
            login_answer=response_login_user1
        )

        response_me_user0: dict[str, Any] = await get_me(auth=user0_auth)

        response_new_chat: dict[str, Any] = await MessageAPI.post_private_chat(
            auth=user1_auth, user_id=response_me_user0["id"], chat_name="Test"
        )

        assert response_new_chat["name"] == "Test"

        (response_delete_chat): dict[
            str, Any
        ] = await MessageAPI.delete_private_chat_by_id(
            auth=user0_auth, chat_id=response_new_chat["id"]
        )

        assert response_delete_chat["id"] == response_new_chat["id"]

    async def test_create_and_delete_chat(self, login: dict[str, str]):
        response_me_user: dict[str, Any] = await get_me(auth=login)

        response_new_chat: dict[str, Any] = await MessageAPI.post_private_chat(
            auth=login, user_id=response_me_user["id"], chat_name="Test"
        )

        assert response_new_chat["name"] == "Test"

        (response_delete_chat): dict[
            str, Any
        ] = await MessageAPI.delete_private_chat_by_id(
            auth=login, chat_id=response_new_chat["id"]
        )

        assert response_delete_chat["id"] == response_new_chat["id"]

    async def test_sending_encrypted_text(
        self, users: list[dict[str, str]], gpg_keys: dict[str, dict[str, PGPKey]]
    ):
        response_login_user0: dict[str, Any] = await login_post(
            email=users[0]["email"], password=users[0]["password"]
        )

        response_login_user1: dict[str, Any] = await login_post(
            email=users[1]["email"], password=users[1]["password"]
        )

        user0_auth: dict[str, str] = generate_login_headers(
            login_answer=response_login_user0
        )
        user1_auth: dict[str, str] = generate_login_headers(
            login_answer=response_login_user1
        )

        response_me_user1: dict[str, Any] = await get_me(auth=user1_auth)

        response_new_chat: dict[str, Any] = await MessageAPI.post_private_chat(
            auth=user0_auth, user_id=response_me_user1["id"], chat_name="Test"
        )

        assert response_new_chat["name"] == "Test"

        response_new_message: dict[str, Any] = await MessageAPI.post_private_message(
            auth=user0_auth,
            chat_id=response_new_chat["id"],
            private_key=gpg_keys[users[0]["email"]]["private"],
            public_key=gpg_keys[users[1]["email"]]["public"],
            message="Test",
        )

        (response_get_events_0): dict[
            str, Any
        ] = await EventsAPI.get_events_private_chats(auth=user1_auth)

        assert response_get_events_0["items"][0]["count"] == 1

        await EventsAPI.mark_readed_private_chat(
            auth=user1_auth, event_id=response_get_events_0["items"][0]["id"]
        )

        (response_get_events_1): dict[
            str, Any
        ] = await EventsAPI.get_events_private_chats(auth=user1_auth)

        assert response_get_events_1["items"][0]["count"] == 0

        (response_get_message_user1): dict[
            str, Any
        ] = await MessageAPI.get_private_messages(
            auth=user1_auth,
            chat_id=response_new_chat["id"],
        )

        encrypted_message_json: dict[str, Any] = response_get_message_user1["items"][0]

        assert (
            response_new_message["encrypted_message"]
            == encrypted_message_json["encrypted_message"]
        )

        assert response_new_message["id"] == encrypted_message_json["id"]

        assert response_new_message["owner_id"] == encrypted_message_json["owner_id"]

        assert (
            response_new_message["creation_datetime"]
            == encrypted_message_json["creation_datetime"]
        )

        assert response_new_chat["id"] == encrypted_message_json["chat_id"]

        (response_delete_chat): dict[
            str, Any
        ] = await MessageAPI.delete_private_chat_by_id(
            auth=user1_auth, chat_id=response_new_chat["id"]
        )

        assert response_delete_chat["id"] == response_new_chat["id"]


class TestMediaAPI:
    def _make_media(self, private_key, encrypted_file):
        sig = private_key.sign(subject=encrypted_file)
        return encrypted_file, bytes(str(sig), "utf-8")

    async def test_upload_and_list_private_media(
        self, users: list[dict[str, str]], gpg_keys: dict[str, dict[str, PGPKey]]
    ):
        response_login_user0: dict[str, Any] = await login_post(
            email=users[0]["email"], password=users[0]["password"]
        )
        response_login_user1: dict[str, Any] = await login_post(
            email=users[1]["email"], password=users[1]["password"]
        )

        user0_auth: dict[str, str] = generate_login_headers(
            login_answer=response_login_user0
        )
        user1_auth: dict[str, str] = generate_login_headers(
            login_answer=response_login_user1
        )

        response_me_user1: dict[str, Any] = await get_me(auth=user1_auth)

        response_new_chat: dict[str, Any] = await MessageAPI.post_private_chat(
            auth=user0_auth, user_id=response_me_user1["id"], chat_name="MediaTest"
        )

        priv_key = gpg_keys[users[0]["email"]]["private"]
        encrypted_file = b"test-encrypted-media-content"
        _, signature = self._make_media(priv_key, encrypted_file)

        upload_result = await MessageAPI.upload_private_media(
            auth=user0_auth,
            chat_id=response_new_chat["id"],
            encrypted_file=encrypted_file,
            signature=signature,
            mime_type="text/plain",
            file_size=len(encrypted_file),
        )

        assert upload_result["id"] is not None
        assert upload_result["mime_type"] == "text/plain"

        response_new_message: dict[str, Any] = await MessageAPI.post_private_message(
            auth=user0_auth,
            chat_id=response_new_chat["id"],
            private_key=priv_key,
            public_key=gpg_keys[users[1]["email"]]["public"],
            message="WithMedia",
        )

        media_list = await MessageAPI.list_private_media(
            auth=user0_auth,
            message_id=response_new_message["id"],
        )

        assert media_list["items"] == []

        response_new_message_with_media = (
            await MessageAPI.post_private_message_with_media(
                auth=user0_auth,
                chat_id=response_new_chat["id"],
                private_key=priv_key,
                public_key=gpg_keys[users[1]["email"]]["public"],
                message="WithMediaLinked",
                media_ids=[upload_result["id"]],
            )
        )

        media_list_after = await MessageAPI.list_private_media(
            auth=user0_auth,
            message_id=response_new_message_with_media["id"],
        )

        assert len(media_list_after["items"]) == 1
        assert media_list_after["items"][0]["id"] == upload_result["id"]

    async def test_upload_and_download_private_media(
        self, users: list[dict[str, str]], gpg_keys: dict[str, dict[str, PGPKey]]
    ):
        response_login_user0: dict[str, Any] = await login_post(
            email=users[0]["email"], password=users[0]["password"]
        )
        response_login_user1: dict[str, Any] = await login_post(
            email=users[1]["email"], password=users[1]["password"]
        )

        user0_auth: dict[str, str] = generate_login_headers(
            login_answer=response_login_user0
        )
        user1_auth: dict[str, str] = generate_login_headers(
            login_answer=response_login_user1
        )

        response_me_user1: dict[str, Any] = await get_me(auth=user1_auth)

        response_new_chat: dict[str, Any] = await MessageAPI.post_private_chat(
            auth=user0_auth, user_id=response_me_user1["id"], chat_name="MediaTest"
        )

        priv_key = gpg_keys[users[0]["email"]]["private"]
        encrypted_file = b"test-encrypted-media-content-download"
        _, signature = self._make_media(priv_key, encrypted_file)

        upload_result = await MessageAPI.upload_private_media(
            auth=user0_auth,
            chat_id=response_new_chat["id"],
            encrypted_file=encrypted_file,
            signature=signature,
            mime_type="text/plain",
            file_size=len(encrypted_file),
        )

        download_result = await MessageAPI.download_private_media(
            auth=user0_auth,
            media_id=upload_result["id"],
        )

        assert download_result["encrypted_file"].encode("utf-8") == encrypted_file
        assert download_result["id"] == upload_result["id"]



    async def test_delete_private_media(
        self, users: list[dict[str, str]], gpg_keys: dict[str, dict[str, PGPKey]]
    ):
        response_login_user0: dict[str, Any] = await login_post(
            email=users[0]["email"], password=users[0]["password"]
        )
        response_login_user1: dict[str, Any] = await login_post(
            email=users[1]["email"], password=users[1]["password"]
        )

        user0_auth: dict[str, str] = generate_login_headers(
            login_answer=response_login_user0
        )
        user1_auth: dict[str, str] = generate_login_headers(
            login_answer=response_login_user1
        )

        response_me_user1: dict[str, Any] = await get_me(auth=user1_auth)

        response_new_chat: dict[str, Any] = await MessageAPI.post_private_chat(
            auth=user0_auth, user_id=response_me_user1["id"], chat_name="MediaTest"
        )

        priv_key = gpg_keys[users[0]["email"]]["private"]
        encrypted_file = b"test-encrypted-media-content-delete"
        _, signature = self._make_media(priv_key, encrypted_file)

        upload_result = await MessageAPI.upload_private_media(
            auth=user0_auth,
            chat_id=response_new_chat["id"],
            encrypted_file=encrypted_file,
            signature=signature,
            mime_type="text/plain",
            file_size=len(encrypted_file),
        )

        delete_result = await MessageAPI.delete_private_media(
            auth=user0_auth,
            media_id=upload_result["id"],
        )

        assert delete_result["id"] == upload_result["id"]

        resp: HttpxResponse = await client.get(
            headers=user0_auth,
            url=f"/messages/private-message/media/{upload_result['id']}",
        )
        assert resp.status_code == 404

    async def test_send_message_with_media(
        self, users: list[dict[str, str]], gpg_keys: dict[str, dict[str, PGPKey]]
    ):
        response_login_user0: dict[str, Any] = await login_post(
            email=users[0]["email"], password=users[0]["password"]
        )
        response_login_user1: dict[str, Any] = await login_post(
            email=users[1]["email"], password=users[1]["password"]
        )

        user0_auth: dict[str, str] = generate_login_headers(
            login_answer=response_login_user0
        )
        user1_auth: dict[str, str] = generate_login_headers(
            login_answer=response_login_user1
        )

        response_me_user1: dict[str, Any] = await get_me(auth=user1_auth)

        response_new_chat: dict[str, Any] = await MessageAPI.post_private_chat(
            auth=user0_auth, user_id=response_me_user1["id"], chat_name="MediaTest"
        )

        priv_key = gpg_keys[users[0]["email"]]["private"]
        pub_key = gpg_keys[users[1]["email"]]["public"]
        encrypted_file = b"test-encrypted-media-content-send"
        _, signature = self._make_media(priv_key, encrypted_file)

        upload_result = await MessageAPI.upload_private_media(
            auth=user0_auth,
            chat_id=response_new_chat["id"],
            encrypted_file=encrypted_file,
            signature=signature,
            mime_type="text/plain",
            file_size=len(encrypted_file),
        )

        message_result = await MessageAPI.post_private_message_with_media(
            auth=user0_auth,
            chat_id=response_new_chat["id"],
            private_key=priv_key,
            public_key=pub_key,
            message="LinkedMedia",
            media_ids=[upload_result["id"]],
        )

        assert message_result["id"] is not None

        media_list = await MessageAPI.list_private_media(
            auth=user0_auth,
            message_id=message_result["id"],
        )

        assert len(media_list["items"]) == 1
        assert media_list["items"][0]["id"] == upload_result["id"]

    async def test_media_file_too_large(
        self, users: list[dict[str, str]], gpg_keys: dict[str, dict[str, PGPKey]]
    ):
        response_login_user0: dict[str, Any] = await login_post(
            email=users[0]["email"], password=users[0]["password"]
        )
        response_login_user1: dict[str, Any] = await login_post(
            email=users[1]["email"], password=users[1]["password"]
        )

        user0_auth: dict[str, str] = generate_login_headers(
            login_answer=response_login_user0
        )
        user1_auth: dict[str, str] = generate_login_headers(
            login_answer=response_login_user1
        )

        response_me_user1: dict[str, Any] = await get_me(auth=user1_auth)

        response_new_chat: dict[str, Any] = await MessageAPI.post_private_chat(
            auth=user0_auth, user_id=response_me_user1["id"], chat_name="MediaTest"
        )

        priv_key = gpg_keys[users[0]["email"]]["private"]
        encrypted_file = b"small-content"
        _, signature = self._make_media(priv_key, encrypted_file)

        resp: HttpxResponse = await client.post(
            headers=user0_auth,
            url=f"/messages/private-message/{response_new_chat['id']}/media/upload",
            json={
                "encrypted_file": encrypted_file.decode("utf-8"),
                "signature": signature.decode("utf-8"),
                "mime_type": "text/plain",
                "file_size": 999999999,
            },
        )

        assert resp.status_code == 413

    async def test_download_media_no_access(
        self, users: list[dict[str, str]], gpg_keys: dict[str, dict[str, PGPKey]]
    ):
        response_login_user0: dict[str, Any] = await login_post(
            email=users[0]["email"], password=users[0]["password"]
        )
        response_login_user1: dict[str, Any] = await login_post(
            email=users[1]["email"], password=users[1]["password"]
        )

        user0_auth: dict[str, str] = generate_login_headers(
            login_answer=response_login_user0
        )
        user1_auth: dict[str, str] = generate_login_headers(
            login_answer=response_login_user1
        )

        response_me_user1: dict[str, Any] = await get_me(auth=user1_auth)

        response_new_chat: dict[str, Any] = await MessageAPI.post_private_chat(
            auth=user0_auth, user_id=response_me_user1["id"], chat_name="MediaTest"
        )

        priv_key = gpg_keys[users[0]["email"]]["private"]
        pub_key = gpg_keys[users[1]["email"]]["public"]
        encrypted_file = b"test-encrypted-media-no-access"
        _, signature = self._make_media(priv_key, encrypted_file)

        upload_result = await MessageAPI.upload_private_media(
            auth=user0_auth,
            chat_id=response_new_chat["id"],
            encrypted_file=encrypted_file,
            signature=signature,
            mime_type="text/plain",
            file_size=len(encrypted_file),
        )

        await MessageAPI.post_private_message_with_media(
            auth=user0_auth,
            chat_id=response_new_chat["id"],
            private_key=priv_key,
            public_key=pub_key,
            message="LinkedForAccess",
            media_ids=[upload_result["id"]],
        )

        third_user_data: dict[str, str] = {
            "user": "user2",
            "email": "user2_media@none.io",
            "password": "1234",
        }
        await create_user_post(third_user_data["email"], third_user_data["password"])
        third_login: dict[str, Any] = await login_post(
            third_user_data["email"], third_user_data["password"]
        )
        third_auth: dict[str, str] = generate_login_headers(third_login)

        resp: HttpxResponse = await client.get(
            headers=third_auth,
            url=f"/messages/private-message/media/{upload_result['id']}",
        )

        assert resp.status_code == 403

    async def test_delete_media_not_owner(
        self, users: list[dict[str, str]], gpg_keys: dict[str, dict[str, PGPKey]]
    ):
        response_login_user0: dict[str, Any] = await login_post(
            email=users[0]["email"], password=users[0]["password"]
        )
        response_login_user1: dict[str, Any] = await login_post(
            email=users[1]["email"], password=users[1]["password"]
        )

        user0_auth: dict[str, str] = generate_login_headers(
            login_answer=response_login_user0
        )
        user1_auth: dict[str, str] = generate_login_headers(
            login_answer=response_login_user1
        )

        response_me_user1: dict[str, Any] = await get_me(auth=user1_auth)

        response_new_chat: dict[str, Any] = await MessageAPI.post_private_chat(
            auth=user0_auth, user_id=response_me_user1["id"], chat_name="MediaTest"
        )

        priv_key_0 = gpg_keys[users[0]["email"]]["private"]
        encrypted_file = b"test-encrypted-media-not-owner"
        _, signature = self._make_media(priv_key_0, encrypted_file)

        upload_result = await MessageAPI.upload_private_media(
            auth=user0_auth,
            chat_id=response_new_chat["id"],
            encrypted_file=encrypted_file,
            signature=signature,
            mime_type="text/plain",
            file_size=len(encrypted_file),
        )

        resp: HttpxResponse = await client.delete(
            headers=user1_auth,
            url=f"/messages/private-message/media/{upload_result['id']}/",
        )

        assert resp.status_code == 403

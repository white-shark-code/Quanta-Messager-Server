import base64
from typing import Any

from httpx import Response as HttpxResponse

from ..events_api import EventsAPI
from ..messages_api import MessageAPI
from ..services import (
    client,
    create_user_post,
    generate_login_headers,
    get_me,
    login_post,
    pgp_encrypt,
    pgp_sign,
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
        self, users: list[dict[str, str]]
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
            sender_user=users[0]["user"],
            recipient_user=users[1]["user"],
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

        # The peer sees the main copy; the POST response carries the
        # sender's self-copy (PGP encryption is randomized, so the two
        # ciphertexts of the same plaintext always differ).
        assert (
            response_new_message["encrypted_message"]
            != encrypted_message_json["encrypted_message"]
        )

        assert response_new_message["id"] == encrypted_message_json["id"]

        assert response_new_message["owner_id"] == encrypted_message_json["owner_id"]

        assert (
            response_new_message["creation_datetime"]
            == encrypted_message_json["creation_datetime"]
        )

        assert response_new_chat["id"] == encrypted_message_json["chat_id"]

        # The sender's own list view returns the same self-copy as the
        # POST response — this is the row their UI can decrypt.
        (response_get_message_user0): dict[
            str, Any
        ] = await MessageAPI.get_private_messages(
            auth=user0_auth,
            chat_id=response_new_chat["id"],
        )

        own_message_json: dict[str, Any] = response_get_message_user0["items"][0]

        assert (
            response_new_message["encrypted_message"]
            == own_message_json["encrypted_message"]
        )
        assert (
            response_new_message["signature"] == own_message_json["signature"]
        )

        (response_delete_chat): dict[
            str, Any
        ] = await MessageAPI.delete_private_chat_by_id(
            auth=user1_auth, chat_id=response_new_chat["id"]
        )

        assert response_delete_chat["id"] == response_new_chat["id"]


class TestMediaAPI:
    async def test_upload_and_list_private_media(
        self, users: list[dict[str, str]]
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

        response_me_user1: dict[str, Any] = await get_me(auth=user0_auth)
        # Note: the original used auth=user1_auth here; we keep user0_auth as creator.

        response_new_chat: dict[str, Any] = await MessageAPI.post_private_chat(
            auth=user0_auth, user_id=response_me_user1["id"], chat_name="MediaTest"
        )

        encrypted_file = b"test-encrypted-media-content"

        upload_result = await MessageAPI.upload_private_media(
            auth=user0_auth,
            chat_id=response_new_chat["id"],
            sender_user=users[0]["user"],
            encrypted_file=encrypted_file,
        )

        assert upload_result["id"] is not None
        assert upload_result["mime_type"] == "text/plain"

        response_new_message: dict[str, Any] = await MessageAPI.post_private_message(
            auth=user0_auth,
            chat_id=response_new_chat["id"],
            sender_user=users[0]["user"],
            recipient_user=users[1]["user"],
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
                sender_user=users[0]["user"],
                recipient_user=users[1]["user"],
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
        self, users: list[dict[str, str]]
    ):
        response_login_user0: dict[str, Any] = await login_post(
            email=users[0]["email"], password=users[0]["password"]
        )

        user0_auth: dict[str, str] = generate_login_headers(
            login_answer=response_login_user0
        )

        response_me_user1: dict[str, Any] = await get_me(
            auth=user0_auth
        )
        # Original used user1_auth — keep this structure here too.

        response_new_chat: dict[str, Any] = await MessageAPI.post_private_chat(
            auth=user0_auth, user_id=response_me_user1["id"], chat_name="MediaTest"
        )

        encrypted_file = b"test-encrypted-media-content-download"

        upload_result = await MessageAPI.upload_private_media(
            auth=user0_auth,
            chat_id=response_new_chat["id"],
            sender_user=users[0]["user"],
            encrypted_file=encrypted_file,
        )

        download_result = await MessageAPI.download_private_media(
            auth=user0_auth,
            media_id=upload_result["id"],
        )

        assert download_result["encrypted_file"].encode("utf-8") == encrypted_file
        assert download_result["id"] == upload_result["id"]

    async def test_delete_private_media(self, users: list[dict[str, str]]):
        response_login_user0: dict[str, Any] = await login_post(
            email=users[0]["email"], password=users[0]["password"]
        )

        user0_auth: dict[str, str] = generate_login_headers(
            login_answer=response_login_user0
        )

        response_me_user1: dict[str, Any] = await get_me(auth=user0_auth)

        response_new_chat: dict[str, Any] = await MessageAPI.post_private_chat(
            auth=user0_auth, user_id=response_me_user1["id"], chat_name="MediaTest"
        )

        encrypted_file = b"test-encrypted-media-content-delete"

        upload_result = await MessageAPI.upload_private_media(
            auth=user0_auth,
            chat_id=response_new_chat["id"],
            sender_user=users[0]["user"],
            encrypted_file=encrypted_file,
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
        self, users: list[dict[str, str]]
    ):
        response_login_user0: dict[str, Any] = await login_post(
            email=users[0]["email"], password=users[0]["password"]
        )

        user0_auth: dict[str, str] = generate_login_headers(
            login_answer=response_login_user0
        )

        response_me_user1: dict[str, Any] = await get_me(auth=user0_auth)

        response_new_chat: dict[str, Any] = await MessageAPI.post_private_chat(
            auth=user0_auth, user_id=response_me_user1["id"], chat_name="MediaTest"
        )

        encrypted_file = b"test-encrypted-media-content-send"

        upload_result = await MessageAPI.upload_private_media(
            auth=user0_auth,
            chat_id=response_new_chat["id"],
            sender_user=users[0]["user"],
            encrypted_file=encrypted_file,
        )

        message_result = await MessageAPI.post_private_message_with_media(
            auth=user0_auth,
            chat_id=response_new_chat["id"],
            sender_user=users[0]["user"],
            recipient_user=users[1]["user"],
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

    async def test_media_file_too_large(self, users: list[dict[str, str]]):
        response_login_user0: dict[str, Any] = await login_post(
            email=users[0]["email"], password=users[0]["password"]
        )

        user0_auth: dict[str, str] = generate_login_headers(
            login_answer=response_login_user0
        )

        response_me_user1: dict[str, Any] = await get_me(auth=user0_auth)

        response_new_chat: dict[str, Any] = await MessageAPI.post_private_chat(
            auth=user0_auth, user_id=response_me_user1["id"], chat_name="MediaTest"
        )

        # The "file_size too large" branch is checked server-side from the
        # JSON body (since /upload_media is a JSON endpoint after the
        # Pydantic migration in an earlier step). It still relies on the
        # signature being valid; bypassing that for a too-large file by
        # signing "small" but reporting huge size.
        from ..services import pgp_sign

        encrypted_file = b"small-content"
        signature = pgp_sign(users[0]["user"], encrypted_file)

        resp: HttpxResponse = await client.post(
            headers=user0_auth,
            url=f"/messages/private-message/{response_new_chat['id']}/media/upload",
            json={
                "encrypted_file": base64.b64encode(encrypted_file).decode("ascii"),
                "signature": base64.b64encode(signature).decode("ascii"),
                "mime_type": "text/plain",
                "file_size": 999_999_999,
            },
        )

        assert resp.status_code == 413

    async def test_download_media_no_access(
        self, users: list[dict[str, str]]
    ):
        response_login_user0: dict[str, Any] = await login_post(
            email=users[0]["email"], password=users[0]["password"]
        )

        user0_auth: dict[str, str] = generate_login_headers(
            login_answer=response_login_user0
        )

        response_me_user1: dict[str, Any] = await get_me(auth=user0_auth)

        response_new_chat: dict[str, Any] = await MessageAPI.post_private_chat(
            auth=user0_auth, user_id=response_me_user1["id"], chat_name="MediaTest"
        )

        encrypted_file = b"test-encrypted-media-no-access"

        upload_result = await MessageAPI.upload_private_media(
            auth=user0_auth,
            chat_id=response_new_chat["id"],
            sender_user=users[0]["user"],
            encrypted_file=encrypted_file,
        )

        await MessageAPI.post_private_message_with_media(
            auth=user0_auth,
            chat_id=response_new_chat["id"],
            sender_user=users[0]["user"],
            recipient_user=users[1]["user"],
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
        self, users: list[dict[str, str]]
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

        response_me_user1: dict[str, Any] = await get_me(auth=user0_auth)

        response_new_chat: dict[str, Any] = await MessageAPI.post_private_chat(
            auth=user0_auth, user_id=response_me_user1["id"], chat_name="MediaTest"
        )

        encrypted_file = b"test-encrypted-media-not-owner"

        # user0 uploads
        upload_result = await MessageAPI.upload_private_media(
            auth=user0_auth,
            chat_id=response_new_chat["id"],
            sender_user=users[0]["user"],
            encrypted_file=encrypted_file,
        )

        # user1 tries to delete user0's media — should be 403
        resp: HttpxResponse = await client.delete(
            headers=user1_auth,
            url=f"/messages/private-message/media/{upload_result['id']}/",
        )
        assert resp.status_code == 403


class TestMessageSignatureRoundTrip:
    """Regression coverage for the ``signature`` column on messages.

    The migration ``6f8a4d2e9c1b_add_signature_to_messages.py`` adds
    a dedicated ``signature`` BYTEA column to ``dialog_messages`` (and
    ``group_messages``) and the response schema ``EncryptedText``
    surfaces it. Before that fix the field was dropped on POST (the
    router never persisted it) and absent from GET responses, which
    left the client unable to verify anything and rendered every
    message as ``🔒 Заблокировано``.
    """

    async def test_post_and_get_round_trip_signature(
        self,
        users: dict[str, Any],
        login: dict[str, str],
    ) -> None:
        # The session-scoped `login` fixture returns user0's bearer
        # headers. user1 is logged in fresh — the standard helper
        # `login_post` issues the second login call inline.
        user0_auth = login
        user1_login = await login_post(email="user1@none.io", password="1234")
        user1_auth = generate_login_headers(user1_login)

        response_me_user1: dict[str, Any] = await get_me(auth=user1_auth)
        chat: dict[str, Any] = await MessageAPI.post_private_chat(
            auth=user0_auth,
            user_id=response_me_user1["id"],
            chat_name="SigTest",
        )

        # user0 sends a real (encrypted + detached-signed) message.
        sent: dict[str, Any] = await MessageAPI.post_private_message(
            auth=user0_auth,
            chat_id=chat["id"],
            sender_user=users[0]["user"],
            recipient_user=users[1]["user"],
            message="hello",
        )

        # POST response must include the signature the backend just stored.
        # It carries the sender's self-copy (decryptable by the sender).
        assert "signature" in sent, sent
        assert sent["signature"] is not None
        assert isinstance(sent["signature"], str)
        # Wire format is base64 of raw detached PGP signature bytes
        # (binary OpenPGP packet, NOT ASCII-armored — `gpg --detach-sign`
        # produces DER output by default). Must round-trip-decode
        # successfully.
        sig_bytes = base64.b64decode(sent["signature"])
        assert len(sig_bytes) > 0

        # GET as the peer must return the main-copy signature (different
        # ciphertext ⇒ different detached signature).
        listed: dict[str, Any] = await MessageAPI.get_private_messages(
            auth=user1_auth,
            chat_id=chat["id"],
        )
        items = listed["items"]
        assert len(items) == 1, listed
        msg = items[0]
        assert "signature" in msg, msg
        assert msg["signature"] is not None
        assert base64.b64decode(msg["signature"]) != sig_bytes

        # GET as the sender must return the same self-copy as POST.
        listed_own: dict[str, Any] = await MessageAPI.get_private_messages(
            auth=user0_auth,
            chat_id=chat["id"],
        )
        own_items = listed_own["items"]
        assert len(own_items) == 1, listed_own
        own_msg = own_items[0]
        assert base64.b64decode(own_msg["signature"]) == sig_bytes
        assert own_msg["encrypted_message"] == sent["encrypted_message"]


class TestMessageSelfCopyValidation:
    """Validation of the sender self-copy on message POST.

    Every message carries two ciphertexts of the same plaintext —
    the main copy (peer-readable) and the self-copy (sender-readable).
    Both detached signatures are verified against the sender's stored
    public key; the self fields are required.
    """

    async def _chat(
        self, user0_auth: dict[str, str], peer_id: str
    ) -> dict[str, Any]:
        return await MessageAPI.post_private_chat(
            auth=user0_auth, user_id=peer_id, chat_name="SelfCopy"
        )

    async def test_post_rejects_tampered_self_signature(
        self, users: list[dict[str, str]]
    ):
        user0_login = await login_post(
            email=users[0]["email"], password=users[0]["password"]
        )
        user1_login = await login_post(
            email=users[1]["email"], password=users[1]["password"]
        )
        user0_auth = generate_login_headers(user0_login)
        user1_auth = generate_login_headers(user1_login)
        me1 = await get_me(auth=user1_auth)

        chat = await self._chat(user0_auth, me1["id"])

        plaintext = b"tamper me"
        encrypted = pgp_encrypt(users[0]["user"], users[1]["user"], plaintext)
        signature = pgp_sign(users[0]["user"], encrypted)
        encrypted_self = pgp_encrypt(users[0]["user"], users[0]["user"], plaintext)
        # Sign *other* bytes so the self-signature does not verify.
        bad_signature_self = pgp_sign(users[0]["user"], b"something else")

        def _b64(data: bytes) -> str:
            return base64.b64encode(data).decode("ascii")

        response = await client.post(
            headers=user0_auth,
            url=f"/messages/private-message/{chat['id']}",
            json={
                "encrypted_message": _b64(encrypted),
                "signature": _b64(signature),
                "encrypted_message_self": _b64(encrypted_self),
                "signature_self": _b64(bad_signature_self),
            },
        )

        assert response.status_code == 422, response.text

    async def test_post_rejects_missing_self_fields(
        self, users: list[dict[str, str]]
    ):
        user0_login = await login_post(
            email=users[0]["email"], password=users[0]["password"]
        )
        user1_login = await login_post(
            email=users[1]["email"], password=users[1]["password"]
        )
        user0_auth = generate_login_headers(user0_login)
        user1_auth = generate_login_headers(user1_login)
        me1 = await get_me(auth=user1_auth)

        chat = await self._chat(user0_auth, me1["id"])

        plaintext = b"no self copy"
        encrypted = pgp_encrypt(users[0]["user"], users[1]["user"], plaintext)
        signature = pgp_sign(users[0]["user"], encrypted)

        def _b64(data: bytes) -> str:
            return base64.b64encode(data).decode("ascii")

        response = await client.post(
            headers=user0_auth,
            url=f"/messages/private-message/{chat['id']}",
            json={
                "encrypted_message": _b64(encrypted),
                "signature": _b64(signature),
            },
        )

        assert response.status_code == 422, response.text

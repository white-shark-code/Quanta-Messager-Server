"""Unit tests for signature verification services (GnuPG backend)."""

import asyncio
import os
import shutil
import subprocess
import tempfile
from contextlib import asynccontextmanager
from contextlib import nullcontext as does_not_raise

import gnupg
import pytest
from fastapi import HTTPException

from src.messages.services import check_media_signature, chech_signature_and_encryption


def _generate_keyring(test_name: str):
    """Return a fresh ``GnupgKeyRing`` for one test, auto-cleaned."""
    from tests.services import GnupgKeyRing  # local to avoid polluting top imports

    kr = GnupgKeyRing()
    kr._test_name = test_name  # type: ignore[attr-defined]
    return kr


@pytest.fixture
def gpg_keyring():
    kr = _generate_keyring("test")
    yield kr
    kr.cleanup()


@asynccontextmanager
async def _wrap(coro):
    """Helper to await an async call in sync test bodies."""
    yield await coro


def _run_async(coro):
    return asyncio.get_event_loop().run_until_complete(coro)


def _make_msg_and_sig(kr, fingerprint: str, payload: bytes):
    """Detach-sign ``payload`` and return ``(message_bytes, signature_bytes)``."""
    sig = kr.sign_detached(fingerprint, payload)
    return payload, sig


def _encrypt(kr, fingerprint: str, plaintext: bytes) -> bytes:
    return kr.encrypt_to(fingerprint, plaintext)


def test_check_media_signature_valid(gpg_keyring):
    fingerprint = gpg_keyring.generate(name="Test media", email="media@none.io")
    public = gpg_keyring.export_public(fingerprint)
    raw = b"test encrypted media content"
    payload, sig = _make_msg_and_sig(gpg_keyring, fingerprint, raw)

    _run_async(
        check_media_signature(
            bytes_file=payload,
            bytes_signature=sig,
            bytes_public_key=public,
        )
    )


def test_check_media_signature_wrong_signature(gpg_keyring):
    fingerprint = gpg_keyring.generate(name="Test media", email="media@none.io")
    public = gpg_keyring.export_public(fingerprint)
    raw = b"tampered content"
    _, sig_for_other = _make_msg_and_sig(gpg_keyring, fingerprint, raw)
    wrong_raw = b"original content"

    with pytest.raises(HTTPException) as exc:
        _run_async(
            check_media_signature(
                bytes_file=wrong_raw,
                bytes_signature=sig_for_other,
                bytes_public_key=public,
            )
        )
    assert exc.value.detail == "Wrong signature, get new public key"


def test_check_media_signature_wrong_public_key(gpg_keyring):
    fingerprint = gpg_keyring.generate(name="A", email="a@e.io")
    public = gpg_keyring.export_public(fingerprint)
    other_fingerprint = gpg_keyring.generate(name="B", email="b@e.io")
    other_private = gpg_keyring.export_private(other_fingerprint)
    raw = b"some content"
    payload, _ = _make_msg_and_sig(gpg_keyring, fingerprint, raw)

    # Sign with WRONG key — public is a's, signature made by b's private
    wrong_sig = gpg_keyring.sign_detached(other_fingerprint, payload)

    with pytest.raises(HTTPException) as exc:
        _run_async(
            check_media_signature(
                bytes_file=payload,
                bytes_signature=wrong_sig,
                bytes_public_key=public,
            )
        )
    assert exc.value.detail == "Wrong signature, get new public key"


def test_chech_signature_and_encryption_valid(gpg_keyring):
    fingerprint = gpg_keyring.generate(name="E", email="e@e.io")
    public = gpg_keyring.export_public(fingerprint)
    plaintext = b"hello world (encrypted)"
    encrypted = _encrypt(gpg_keyring, fingerprint, plaintext)
    sig = gpg_keyring.sign_detached(fingerprint, encrypted)

    _run_async(
        chech_signature_and_encryption(
            bytes_message=encrypted,
            bytes_signature=sig,
            bytes_public_key=public,
        )
    )


def test_chech_signature_and_encryption_wrong_signature(gpg_keyring):
    fingerprint = gpg_keyring.generate(name="E", email="e@e.io")
    public = gpg_keyring.export_public(fingerprint)
    encrypted = _encrypt(gpg_keyring, fingerprint, b"plaintext")
    # Sign something different than what gets sent
    wrong_sig = gpg_keyring.sign_detached(fingerprint, b"different-data")

    with pytest.raises(HTTPException) as exc:
        _run_async(
            chech_signature_and_encryption(
                bytes_message=encrypted,
                bytes_signature=wrong_sig,
                bytes_public_key=public,
            )
        )
    assert exc.value.detail == "Wrong signature, get new public key"


def test_chech_signature_and_encryption_unencrypted_message(gpg_keyring):
    fingerprint = gpg_keyring.generate(name="E", email="e@e.io")
    public = gpg_keyring.export_public(fingerprint)
    # Plain text not starting with "-----BEGIN PGP MESSAGE-----"
    not_encrypted = b"just plain text, not armored"
    sig = gpg_keyring.sign_detached(fingerprint, not_encrypted)

    with pytest.raises(HTTPException) as exc:
        _run_async(
            chech_signature_and_encryption(
                bytes_message=not_encrypted,
                bytes_signature=sig,
                bytes_public_key=public,
            )
        )
    assert exc.value.detail == "Message not encrypted"

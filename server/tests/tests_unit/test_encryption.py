from contextlib import contextmanager
from contextlib import nullcontext as does_not_raise

from fastapi import HTTPException
from pgpy import PGPUID, PGPKey
from pgpy.constants import (
    CompressionAlgorithm,
    HashAlgorithm,
    KeyFlags,
    PubKeyAlgorithm,
    SymmetricKeyAlgorithm,
)
from pytest import mark, raises

from src.messages.services import chech_signature_and_encryption, check_media_signature

right_message: bytes = b"-----BEGIN PGP MESSAGE-----\n\nwYwDctMFi+NIZvsBA/9Bkfo+MrEmVjvaBNWqN77HWriguWd2UuwLhs7BpgpWpI36\nczDz6zhVEXHa/ResXMTViGVkXIVMVTRwpJb5nI/DPz+DzDOaBik79MjJ/H5+nSbF\nm3VM82pFCy3XCGDzwm8lcCBLaiO7ub8hYU4f1M0X1neK0K1CC+SbLYlkW5GzjdIy\nAXkmmCyUDUGHRSRSCVSC4sOymXOpDDJNjnz4py6VT/GuT5q4HxIc9xciQEgCqKsk\nNyc=\n=CDvT\n-----END PGP MESSAGE-----\n"  # noqa
right_public_key: bytes = b"-----BEGIN PGP PUBLIC KEY BLOCK-----\n\nxo0EaHs2WwEEANWgMqlKQLGyjY5ospvQ2WVSCBMvKpC7ljz/o8U4hXmPCBXS3fEC\nhlFRVA+jch/2s0pnVGtSu+WB/r48Ujg8rdUjYyZDeClypwngRW0NnBxW2Zjvl/06\n+JhlRPcJ0ahEgnkrFBfrGKJFvDr7humOmBzfqUA/36UjBl6cMpZ1yuAtABEBAAHN\nJ1Rlc3QgdXNlcjAgKFF1YW50IHRlc3QpIDx1c2VyMEBub25lLmlvPsLABQQTAQgA\nLwUCaHs2WwIbDgUVCAkKCwUWAwIBAAIeARYhBMCfOC4Othj0e6ukGiSkGApcbmzg\nAAoJECSkGApcbmzgbJYD/2V+9AmM8jzHIb10KDdBT251LnjEeJ6UlbGc6EM31Rlc\nElJ6I4703aDZ+8ev+97V6tFgf1M5ds/wYoJYvSRB5Vmc3CeH5TbGXJxyyEcDljGP\np30iAPTCQwbiYUJ3TmBPzshRuYvjKohvz7z7YtryQCRPPHhRcK80wVmWqU9QZW8g\n=wCpj\n-----END PGP PUBLIC KEY BLOCK-----\n"  # noqa
right_signature: bytes = b"-----BEGIN PGP SIGNATURE-----\n\nwrMEAAEIAB0FAmh7NlwWIQTAnzguDrYY9HurpBokpBgKXG5s4AAKCRAkpBgKXG5s\n4MHKA/4+c/oGd1Qyn6+J2jaN2SY+BcwqhK7Pdk/MdbAJB9m87BG27Uh73B0dkmuj\nOs4Flv9visZxDy7qCztn9vF6DLjFAymjDvKdgjuJGF/gv/V7MURJLPJWj2xluwcj\nOR9dMWw6ALjkzb5QzoHGu2+7/Xo/v0gfipPIoV0w71s4vfKqoQ==\n=BhON\n-----END PGP SIGNATURE-----\n"  # noqa

spy_message: bytes = b"-----BEGIN PGP MESSAGE-----\n\nwYwDctMFi+NIZvsBA/9Bkfo+MrEmVjvaBNWqN77HWriguWd2UuwLhs7BpgpWpI36\nczDz6zhVEXHa/ResXMTViGVkXIVMVTRwpJb5nI/DPz+DzDOaBik79MjJ/H5+nSbF\nm3VM82pFCy3XCGDzwm8lcCBLaiO7ub8hYU4f1M0X1neK0K1CC+SbLYlkW5GzjdIy\nAXkmmCyUDUGHRSRSCVSC4sOymXOpDDJNjnz4py6VT/fdf5q4HxIc9xciQEgCqKsk\nNyc=\n=TdvT\n-----END PGP MESSAGE-----\n"  # noqa
wrong_public_key: bytes = b"-----BEGIN PGP PUBLIC KEY BLOCK-----\n\nxo0EaHs2WwEEANWgMqlKQLGyjY5ospvQ2WVSCBMvKpC8oXf/o8U4hXmPCBXS3fEC\nhlFRVA+jch/2s0pnVGtSu+WB/r48Ujg8rdUjYyZDeClypwngRW0NnBxW2Zjvl/06\n+JhlRPcJ0ahEgnkrFBfrGKJFvDr7humOmBzfqUA/36UjBl6cMpZ1yuAtABEBAAHN\nJ1Rlc3QgdXNlcjAgKFF1YW50IHRlc3QpIDx1c2VyMEBub25lLmlvPsLABQQTAQgA\nLwUCaHs2WwIbDgUVCAkKCwUWAwIBAAIeARYhBMCfOC4Othj0e6ukGiSkGApcbmzg\nAAoJECSkGApcbmzgbJYD/2V+9AmM8jzHIb10KDdBT251LnjEeJ6UlbGc6EM31Rlc\nElJ6I4703aDZ+8ev+97V6tFgf1M5ds/wYoJYvSRB5Vmc3CeH5TbGXJxyyEcDljGP\np30iAPTCQwbiYUJ3TmBPzshRuYvjKohvz7z7YtryQCRPPHhRcK80wVmWqU9QZW8g\n=wCpj\n-----END PGP PUBLIC KEY BLOCK-----\n"  # noqa
wrong_signature: bytes = b"-----BEGIN PGP SIGNATURE-----\n\nwwOEAAEIAB0FAmh7NlwWIQTAnzguDrYY9HurpBokpBgKXG5s4AAKCRAkpBgKXG5s\n4MHKA/4+c/oGd1Qyn6+J2jaN2SY+BcwqhK7Pdk/MdbAJB9m87BG27Uh73B0dkmuj\nOs4Flv9visZxDy7qCztn9vF6DLjFAymjDvKdgjuJGF/gv/V7MURJLPJWj2xluwcj\nOR9dMWw6ALjkzb5QzoHGu2+7/Xo/v0gfipPIoV0w71s4vfKqoQ==\n=BhON\n-----END PGP SIGNATURE-----\n"  # noqa

detail_var0: str = "Wrong expected: signature. got: opaque, get new public key"
detail_var1: str = "Wrong signature, get new public key"
detail_var2: str = "Warning!!! Not correct PGPKey!"


@mark.parametrize(
    "bytes_message, bytes_signature, bytes_public_key, expectation, detail",
    [
        (right_message, right_signature, right_public_key, does_not_raise(), None),
        (
            right_message,
            wrong_signature,
            right_public_key,
            raises(HTTPException),
            detail_var0,
        ),
        (
            spy_message,
            right_signature,
            right_public_key,
            raises(HTTPException),
            detail_var1,
        ),
        (
            right_message,
            right_signature,
            wrong_public_key,
            raises(HTTPException),
            detail_var2,
        ),
    ],
)
def test_chech_signature_and_encryption(
    bytes_message: bytes,
    bytes_signature: bytes,
    bytes_public_key: bytes,
    expectation: contextmanager,
    detail: str | None,
):
    with expectation as exc_info:
        chech_signature_and_encryption(bytes_message, bytes_signature, bytes_public_key)

    if detail:
        assert exc_info.value.detail == detail


def _generate_media_keys():
    key = PGPKey.new(key_algorithm=PubKeyAlgorithm.RSAEncryptOrSign, key_size=1024)
    uid = PGPUID.new(pn="Test media", comment="Quant test", email="media@none.io")
    key.add_uid(
        uid=uid,
        usage=[KeyFlags.Sign, KeyFlags.EncryptCommunications, KeyFlags.EncryptStorage],
        hashes=[HashAlgorithm.SHA256],
        chiphers=[SymmetricKeyAlgorithm.AES256],
        compression=[CompressionAlgorithm.Uncompressed],
    )
    return key, key.pubkey


def test_check_media_signature_valid():
    private_key, public_key = _generate_media_keys()
    raw_bytes = b"test encrypted media content"
    signature = private_key.sign(subject=raw_bytes)
    check_media_signature(
        bytes_file=raw_bytes,
        bytes_signature=bytes(str(signature), "utf-8"),
        bytes_public_key=bytes(str(public_key), "utf-8"),
    )


def test_check_media_signature_wrong_signature():
    private_key, public_key = _generate_media_keys()
    raw_bytes = b"test encrypted media content"
    wrong_raw = b"tampered content"
    signature = private_key.sign(subject=wrong_raw)
    with raises(HTTPException) as exc_info:
        check_media_signature(
            bytes_file=raw_bytes,
            bytes_signature=bytes(str(signature), "utf-8"),
            bytes_public_key=bytes(str(public_key), "utf-8"),
        )
    assert exc_info.value.detail == "Wrong signature, get new public key"


def test_check_media_signature_wrong_public_key():
    private_key, public_key = _generate_media_keys()
    _, wrong_public_key = _generate_media_keys()
    raw_bytes = b"test encrypted media content"
    signature = private_key.sign(subject=raw_bytes)
    with raises(HTTPException) as exc_info:
        check_media_signature(
            bytes_file=raw_bytes,
            bytes_signature=bytes(str(signature), "utf-8"),
            bytes_public_key=bytes(str(wrong_public_key), "utf-8"),
        )
    assert exc_info.value.detail == "Warning!!! Not correct PGPKey!"

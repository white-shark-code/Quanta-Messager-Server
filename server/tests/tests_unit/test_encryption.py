from contextlib import contextmanager
from contextlib import nullcontext as does_not_raise

from fastapi import HTTPException
from pytest import mark, raises

from src.messages.services import chech_signature_and_encryption

right_message: bytes = b'-----BEGIN PGP MESSAGE-----\n\nwYwDctMFi+NIZvsBA/9Bkfo+MrEmVjvaBNWqN77HWriguWd2UuwLhs7BpgpWpI36\nczDz6zhVEXHa/ResXMTViGVkXIVMVTRwpJb5nI/DPz+DzDOaBik79MjJ/H5+nSbF\nm3VM82pFCy3XCGDzwm8lcCBLaiO7ub8hYU4f1M0X1neK0K1CC+SbLYlkW5GzjdIy\nAXkmmCyUDUGHRSRSCVSC4sOymXOpDDJNjnz4py6VT/GuT5q4HxIc9xciQEgCqKsk\nNyc=\n=CDvT\n-----END PGP MESSAGE-----\n' #noqa
right_public_key: bytes = b'-----BEGIN PGP PUBLIC KEY BLOCK-----\n\nxo0EaHs2WwEEANWgMqlKQLGyjY5ospvQ2WVSCBMvKpC7ljz/o8U4hXmPCBXS3fEC\nhlFRVA+jch/2s0pnVGtSu+WB/r48Ujg8rdUjYyZDeClypwngRW0NnBxW2Zjvl/06\n+JhlRPcJ0ahEgnkrFBfrGKJFvDr7humOmBzfqUA/36UjBl6cMpZ1yuAtABEBAAHN\nJ1Rlc3QgdXNlcjAgKFF1YW50IHRlc3QpIDx1c2VyMEBub25lLmlvPsLABQQTAQgA\nLwUCaHs2WwIbDgUVCAkKCwUWAwIBAAIeARYhBMCfOC4Othj0e6ukGiSkGApcbmzg\nAAoJECSkGApcbmzgbJYD/2V+9AmM8jzHIb10KDdBT251LnjEeJ6UlbGc6EM31Rlc\nElJ6I4703aDZ+8ev+97V6tFgf1M5ds/wYoJYvSRB5Vmc3CeH5TbGXJxyyEcDljGP\np30iAPTCQwbiYUJ3TmBPzshRuYvjKohvz7z7YtryQCRPPHhRcK80wVmWqU9QZW8g\n=wCpj\n-----END PGP PUBLIC KEY BLOCK-----\n' #noqa
right_signature: bytes = b'-----BEGIN PGP SIGNATURE-----\n\nwrMEAAEIAB0FAmh7NlwWIQTAnzguDrYY9HurpBokpBgKXG5s4AAKCRAkpBgKXG5s\n4MHKA/4+c/oGd1Qyn6+J2jaN2SY+BcwqhK7Pdk/MdbAJB9m87BG27Uh73B0dkmuj\nOs4Flv9visZxDy7qCztn9vF6DLjFAymjDvKdgjuJGF/gv/V7MURJLPJWj2xluwcj\nOR9dMWw6ALjkzb5QzoHGu2+7/Xo/v0gfipPIoV0w71s4vfKqoQ==\n=BhON\n-----END PGP SIGNATURE-----\n' #noqa

spy_message: bytes = b'-----BEGIN PGP MESSAGE-----\n\nwYwDctMFi+NIZvsBA/9Bkfo+MrEmVjvaBNWqN77HWriguWd2UuwLhs7BpgpWpI36\nczDz6zhVEXHa/ResXMTViGVkXIVMVTRwpJb5nI/DPz+DzDOaBik79MjJ/H5+nSbF\nm3VM82pFCy3XCGDzwm8lcCBLaiO7ub8hYU4f1M0X1neK0K1CC+SbLYlkW5GzjdIy\nAXkmmCyUDUGHRSRSCVSC4sOymXOpDDJNjnz4py6VT/fdf5q4HxIc9xciQEgCqKsk\nNyc=\n=TdvT\n-----END PGP MESSAGE-----\n' #noqa
wrong_public_key: bytes = b'-----BEGIN PGP PUBLIC KEY BLOCK-----\n\nxo0EaHs2WwEEANWgMqlKQLGyjY5ospvQ2WVSCBMvKpC8oXf/o8U4hXmPCBXS3fEC\nhlFRVA+jch/2s0pnVGtSu+WB/r48Ujg8rdUjYyZDeClypwngRW0NnBxW2Zjvl/06\n+JhlRPcJ0ahEgnkrFBfrGKJFvDr7humOmBzfqUA/36UjBl6cMpZ1yuAtABEBAAHN\nJ1Rlc3QgdXNlcjAgKFF1YW50IHRlc3QpIDx1c2VyMEBub25lLmlvPsLABQQTAQgA\nLwUCaHs2WwIbDgUVCAkKCwUWAwIBAAIeARYhBMCfOC4Othj0e6ukGiSkGApcbmzg\nAAoJECSkGApcbmzgbJYD/2V+9AmM8jzHIb10KDdBT251LnjEeJ6UlbGc6EM31Rlc\nElJ6I4703aDZ+8ev+97V6tFgf1M5ds/wYoJYvSRB5Vmc3CeH5TbGXJxyyEcDljGP\np30iAPTCQwbiYUJ3TmBPzshRuYvjKohvz7z7YtryQCRPPHhRcK80wVmWqU9QZW8g\n=wCpj\n-----END PGP PUBLIC KEY BLOCK-----\n' #noqa
wrong_signature: bytes = b'-----BEGIN PGP SIGNATURE-----\n\nwwOEAAEIAB0FAmh7NlwWIQTAnzguDrYY9HurpBokpBgKXG5s4AAKCRAkpBgKXG5s\n4MHKA/4+c/oGd1Qyn6+J2jaN2SY+BcwqhK7Pdk/MdbAJB9m87BG27Uh73B0dkmuj\nOs4Flv9visZxDy7qCztn9vF6DLjFAymjDvKdgjuJGF/gv/V7MURJLPJWj2xluwcj\nOR9dMWw6ALjkzb5QzoHGu2+7/Xo/v0gfipPIoV0w71s4vfKqoQ==\n=BhON\n-----END PGP SIGNATURE-----\n' #noqa

detail_var0: str = 'Wrong expected: signature. got: opaque, get new public key'
detail_var1: str = 'Wrong signature, get new public key'
detail_var2: str = 'Warning!!! Not correct PGPKey!'

@mark.parametrize(
    'bytes_message, bytes_signature, bytes_public_key, expectation, detail',
    [
        (
            right_message,
            right_signature,
            right_public_key,
            does_not_raise(),
            None
        ),
        (
            right_message,
            wrong_signature,
            right_public_key,
            raises(HTTPException),
            detail_var0
        ),
        (
            spy_message,
            right_signature,
            right_public_key,
            raises(HTTPException),
            detail_var1
        ),
        (
            right_message,
            right_signature,
            wrong_public_key,
            raises(HTTPException),
            detail_var2
        )
    ]
)
def test_chech_signature_and_encryption(
    bytes_message: bytes,
    bytes_signature: bytes,
    bytes_public_key: bytes,
    expectation: contextmanager,
    detail: str | None
):
    with expectation as exc_info:
        chech_signature_and_encryption(
            bytes_message,
            bytes_signature,
            bytes_public_key
        )

    if detail:
        assert exc_info.value.detail == detail

"""Message signature verification and encryption validation services.

Uses GnuPG 2.4+ via :mod:`shared.pgp` to verify detached PGP
signatures on messages and media files. Both checks return 422 on
signature failure (so the client can prompt the user to fetch a
fresh public key from the server).

Сервисы проверки PGP-подписей сообщений и валидации шифрования.
"""

from fastapi import HTTPException, status

from shared.pgp import get_backend, is_encrypted_pgp_message


async def chech_signature_and_encryption(
    bytes_message: bytes, bytes_signature: bytes, bytes_public_key: bytes
):
    """Verify the message signature and confirm the payload is encrypted.

    Args:
        bytes_message: Encrypted message payload (raw bytes of an
            ASCII-armored ``-----BEGIN PGP MESSAGE-----`` block).
        bytes_signature: Detached PGP signature for the message.
        bytes_public_key: ASCII-armored public key of the signer.

    Raises:
        HTTPException: 422 if signature does not verify.
        HTTPException: 422 if the message is not encrypted.

    Raises when the GnuPG backend cannot validate the signature or
    when the payload does not look like an encrypted OpenPGP message.

    Проверяет подпись сообщения и то, что оно зашифровано.
    """
    backend = get_backend()
    is_valid, _stderr = await backend.verify(
        bytes_message, bytes_signature, bytes_public_key
    )
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Wrong signature, get new public key",
        )

    if not is_encrypted_pgp_message(bytes_message):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Message not encrypted",
        )


async def check_media_signature(
    bytes_file: bytes, bytes_signature: bytes, bytes_public_key: bytes
):
    """Verify the detached PGP signature of an encrypted media file.

    Args:
        bytes_file: Encrypted media payload bytes.
        bytes_signature: Detached PGP signature for the file.
        bytes_public_key: ASCII-armored public key of the signer.

    Raises:
        HTTPException: 422 if the GnuPG backend cannot verify the
            signature.

    Проверяет отделённую PGP-подпись зашифрованного медиа-файла.
    """
    backend = get_backend()
    is_valid, _stderr = await backend.verify(
        bytes_file, bytes_signature, bytes_public_key
    )
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Wrong signature, get new public key",
        )

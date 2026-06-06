"""Message signature verification and encryption validation services.

Сервисы проверки подписи сообщений и валидации шифрования.
"""
from fastapi import HTTPException, status
from pgpy import PGPKey, PGPMessage, PGPSignature
from pgpy.errors import PGPError


def chech_signature_and_encryption(
    bytes_message: bytes,
    bytes_signature: bytes,
    bytes_public_key: bytes
):
    """Verify message signature and check encryption status.

    Проверяет подпись сообщения и статус шифрования.

    Args:
        bytes_message: Encrypted message as bytes.
            Зашифрованное сообщение в виде байтов.
        bytes_signature: Message signature as bytes.
            Подпись сообщения в виде байтов.
        bytes_public_key: Public key for verification as bytes.
            Публичный ключ для проверки в виде байтов.

    Raises:
        HTTPException: If message parsing fails, signature is invalid,
            or message is not encrypted.
            Если разбор сообщения не удался, подпись недействительна
            или сообщение не зашифровано.
    """
    try:
        message: PGPMessage = PGPMessage.from_blob(blob = bytes_message)
        signature: PGPSignature = PGPSignature.from_blob(blob = bytes_signature)
        public_key: PGPKey = PGPKey.from_blob(blob = bytes_public_key)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f'Wrong {str(exc.args[0]).lower()}, get new public key'
        )

    try:
        if not public_key[0].verify(
            subject = bytes(message),
            signature = signature
        ):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail='Wrong signature, get new public key'
            )
    except PGPError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail='Warning!!! Not correct PGPKey!'
        )

    if not message.is_encrypted:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail='Message not encrypted'
        )

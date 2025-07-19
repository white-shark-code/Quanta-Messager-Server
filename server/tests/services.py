from __future__ import annotations

import contextlib
from abc import ABCMeta
from typing import Any, ClassVar

import loguru
from fastapi.testclient import TestClient
from httpx import Response
from pgpy import PGPUID, PGPKey
from pgpy.constants import (
    CompressionAlgorithm,
    HashAlgorithm,
    KeyFlags,
    PubKeyAlgorithm,
    SymmetricKeyAlgorithm,
)

from src.database import get_async_session
from src.main import app

client: TestClient = TestClient(app=app)

logger_obj: loguru.Logger = loguru.logger

logger_obj.add(
    sink='../test_logs.log',
    format='{time} {level} {message}',
    level='DEBUG'
)

get_async_session_context = contextlib.asynccontextmanager(get_async_session)

def create_user_post(email: str, password: str) -> dict[str, Any]:
    response: Response = client.post(
        url='/auth/register',
        json={
            'email': email,
            'password': password,
            'is_active': True,
            'is_superuser': False,
            'is_verified': False
        }
    )

    assert response.status_code == 201 or response.status_code == 400

    data_json: dict[str, str] = response.json()

    logger_obj.debug(f'User been created {data_json}')

    return data_json

def generate_login_headers(login_answer: dict[str, Any]) -> dict[str, str]:
    return {'Authorization': f'Bearer {login_answer['access_token']}'}

def login_post(email: str, password: str) -> dict[str, Any]:
    response: Response = client.post(
        url='/auth/login',
        headers={
            'Content-Type': 'application/x-www-form-urlencoded',
        },
        data=f'grant_type=password&username={email}&password={password}&scope=&client_id=string&client_secret=string'
    )

    assert response.status_code == 200

    return response.json()

def get_me(auth: dict[str, str]) -> dict[str, Any]:
    response: Response = client.get(
        url='/users/me',
        headers=auth
    )

    assert response.status_code == 200

    return response.json()

def change_user_public_key_post(
    auth: dict[str, str],
    public_key: PGPKey
) -> dict[str, Any]:
    login_headers: dict[str, str] = generate_login_headers(auth)
    public_key_bytes: bytes = bytes(str(public_key), encoding='utf-8')
    response: Response = client.post(
        url = '/auth/change-public-key',
        headers = {
            'accept': 'application/json',
        } | login_headers,
        files = {
            'new_public_key': public_key_bytes
        }
    )

    assert response.status_code == 200

    return response.json()

def generate_pgp_keys(email: str, user: str) -> tuple[PGPKey]:
    key: PGPKey = PGPKey.new(
        key_algorithm=PubKeyAlgorithm.RSAEncryptOrSign,
        key_size=1024
    )
    uid: PGPUID = PGPUID.new(
        pn=f'Test {user}',
        comment='Quant test',
        email=email
    )
    key.add_uid(
        uid=uid,
        usage=[
            KeyFlags.Sign,
            KeyFlags.EncryptCommunications,
            KeyFlags.EncryptStorage
        ],
        hashes=[
            HashAlgorithm.SHA256,
            HashAlgorithm.SHA384,
            HashAlgorithm.SHA512,
            HashAlgorithm.SHA224
        ],
        chiphers=[
            SymmetricKeyAlgorithm.AES256,
            SymmetricKeyAlgorithm.AES192,
            SymmetricKeyAlgorithm.AES128
        ],
        compression=[
            CompressionAlgorithm.BZ2,
            CompressionAlgorithm.ZLIB,
            CompressionAlgorithm.ZIP,
            CompressionAlgorithm.Uncompressed
        ]
    )

    return (key, key.pubkey)


class BasicAPI(metaclass=ABCMeta):
    pass

class SingletonMeta(type):

        _instances: ClassVar[dict[Any, object]] = {}

        def __call__(cls, *args, **kwargs):
            if cls not in cls._instances:
                instance = super().__call__(*args, **kwargs)
                cls._instances[cls] = instance
            return cls._instances[cls]

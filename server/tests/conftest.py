from os import remove
from typing import Any

from alembic.command import upgrade
from alembic.config import Config
from pgpy import PGPKey
from pytest import fixture

from src.settings import cfg

from .services import (
        SingletonMeta,
        change_user_public_key_post,
        create_user_post,
        generate_login_headers,
        generate_pgp_keys,
        login_post,
)


class SingletonKeys(metaclass=SingletonMeta):
        def __init__(self, users: list[dict[str, str]]):
            self._gpg_keys: dict[str, dict[str, PGPKey]] = {}

            for user in users:
                keys_user: tuple[PGPKey] = generate_pgp_keys(
                    email=user['email'],
                    user=user['user']
                )

                self._gpg_keys[user['email']] = \
                    {
                        'private': keys_user[0],
                        'public': keys_user[1],
                    }

        @property
        def gpg_keys(self) -> dict[str, dict[str, PGPKey]]:
            return self._gpg_keys


@fixture(scope='session', autouse=True)
def setup_database():
    assert cfg.DEBUG
    alembic_config: Config = Config(file_='alembic.ini')
    try:
        remove(path='test.db')
    except FileNotFoundError:
        pass
    upgrade(config=alembic_config, revision='head')

@fixture
def users() -> list[dict[str, str]]:
    return [
        {
            'user': 'user0',
            'email': 'user0@none.io',
            'password': '1234'
        },
        {
            'user': 'user1',
            'email': 'user1@none.io',
            'password': '1234'
        }
    ]

@fixture
def gpg_keys(users: list[dict[str, str]]) -> dict[str, dict[str, PGPKey]]:
    return SingletonKeys(users).gpg_keys

@fixture
def create_users(
    users: list[dict[str, str]],
    gpg_keys: dict[str, dict[str, PGPKey]]
):

    create_user_post(
        users[0]['email'],
        users[0]['password']
    )

    create_user_post(
        users[1]['email'],
        users[1]['password']
    )

    auth_user0: dict[str, Any] = login_post(
        users[0]['email'],
        users[0]['password']
    )

    auth_user1: dict[str, Any] = login_post(
        users[1]['email'],
        users[1]['password']
    )

    keys_user0: dict[str, PGPKey] = gpg_keys[users[0]['email']]

    keys_user1: dict[str, PGPKey] = gpg_keys[users[1]['email']]

    change_user_public_key_post(
        auth=auth_user0,
        public_key=keys_user0['public']
    )

    change_user_public_key_post(
        auth=auth_user1,
        public_key=keys_user1['public']
    )

@fixture
def login() -> dict[str, str]:
    responce_json: dict[str, str] = login_post(
        email='user0@none.io',
        password='1234'
    )

    return generate_login_headers(responce_json)

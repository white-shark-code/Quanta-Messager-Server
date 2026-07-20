"""Sync data fixtures shared between unit and integration tests.

Общие sync-фикстуры данных для unit и integration тестов.
"""

from typing import Any, ClassVar

from pgpy import PGPKey
from pytest import fixture

from .services import SingletonMeta, generate_pgp_keys


class SingletonKeys(metaclass=SingletonMeta):
    def __init__(self, users: list[dict[str, str]]):
        self._gpg_keys: dict[str, dict[str, PGPKey]] = {}

        for user in users:
            keys_user: tuple[PGPKey] = generate_pgp_keys(
                email=user["email"], user=user["user"]
            )

            self._gpg_keys[user["email"]] = {
                "private": keys_user[0],
                "public": keys_user[1],
            }

    @property
    def gpg_keys(self) -> dict[str, dict[str, PGPKey]]:
        return self._gpg_keys


@fixture(scope="session")
def users() -> list[dict[str, str]]:
    return [
        {"user": "user0", "email": "user0@none.io", "password": "1234"},
        {"user": "user1", "email": "user1@none.io", "password": "1234"},
    ]


@fixture(scope="session")
def gpg_keys(users: list[dict[str, str]]) -> dict[str, dict[str, PGPKey]]:
    return SingletonKeys(users).gpg_keys

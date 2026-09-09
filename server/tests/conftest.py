"""Sync data fixtures shared between unit and integration tests.

Общие sync-фикстуры данных для unit и integration тестов.
"""

from pathlib import Path

from pytest import fixture

from .services import (
    generate_pgp_keys,
    get_pgp_keyring,
    get_pgp_fingerprint,
    cleanup_pgp_keys,
)


class SingletonKeys:
    """Holds isolated GnuPG keyrings for each test user.

    The keys are generated via :func:`tests.services.generate_pgp_keys`
    on first use and cached for the test session.
    """

    def __init__(self, users: list[dict[str, str]]):
        self._gpg_keys: dict[str, dict[str, bytes]] = {}

        for user in users:
            private_key: bytes
            public_key: bytes
            private_key, public_key = generate_pgp_keys(
                email=user["email"], user=user["user"]
            )
            self._gpg_keys[user["email"]] = {
                "private": private_key,
                "public": public_key,
            }

    @property
    def gpg_keys(self) -> dict[str, dict[str, bytes]]:
        return self._gpg_keys


@fixture(scope="session")
def users() -> list[dict[str, str]]:
    return [
        {"user": "user0", "email": "user0@none.io", "password": "1234"},
        {"user": "user1", "email": "user1@none.io", "password": "1234"},
    ]


@fixture(scope="session")
def gpg_keys(users: list[dict[str, str]]) -> dict[str, dict[str, bytes]]:
    return SingletonKeys(users).gpg_keys

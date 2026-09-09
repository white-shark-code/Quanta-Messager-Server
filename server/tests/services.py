from __future__ import annotations

import contextlib
import os
import shutil
import subprocess
import tempfile
import uuid
from abc import ABCMeta
from pathlib import Path
from typing import Any, ClassVar

import gnupg
import loguru
from httpx import ASGITransport, AsyncClient, Response

from src.main import app

client: AsyncClient = AsyncClient(
    transport=ASGITransport(app=app), base_url="http://test"
)

logger_obj: loguru.Logger = loguru.logger

logger_obj.add(
    sink="../test_logs.log", format="{time} {level} {message}", level="DEBUG"
)


class GnupgKeyRing:
    """Per-instance GnuPG homedir for isolated test key generation.

    Provides ``generate``, ``sign``, ``encrypt`` helpers that work in
    a temporary homedir so different test fixtures get independent
    keys without leaking into the system keyring.

    Изолированный per-instance homedir GnuPG для генерации тестовых
    ключей и подписей.
    """

    def __init__(self) -> None:
        self.homedir = Path(tempfile.mkdtemp(prefix="quant-test-gpg-"))
        os.chmod(self.homedir, 0o700)
        self.gpg = gnupg.GPG(gnupghome=str(self.homedir))
        self.gpg.encoding = "utf-8"

    def generate(self, name: str, email: str, key_length: int = 1024) -> str:
        """Generate a new key in this homedir, return the fingerprint."""
        passphrase = "test-passphrase-quant"
        result = self.gpg.gen_key(
            self.gpg.gen_key_input(
                name_real=name,
                name_email=email,
                name_comment="Quant test",
                key_type="RSA",
                key_length=key_length,
                expire_date=0,
                passphrase=passphrase,
            )
        )
        if not result or not str(result):
            stderr = getattr(result, "stderr", "n/a") if result else "n/a"
            raise RuntimeError(f"Failed to generate key: stderr={stderr}")
        fingerprint = str(result)
        self.passphrase = passphrase
        return fingerprint

    def export_public(self, fingerprint: str) -> bytes:
        return str(self.gpg.export_keys(fingerprint)).encode("utf-8")

    def export_private(self, fingerprint: str) -> bytes:
        passphrase = getattr(self, "passphrase", "test-passphrase-quant")
        return str(
            self.gpg.export_keys(
                fingerprint, secret=True, passphrase=passphrase
            )
        ).encode("utf-8")

    def sign_detached(self, fingerprint: str, message: bytes) -> bytes:
        """Run ``gpg --detach-sign`` and return armored signature bytes."""
        with tempfile.NamedTemporaryFile(
            delete=False, dir=self.homedir
        ) as mf:
            mf.write(message)
            msg_path = mf.name
        sig_path = msg_path + ".asc"
        try:
            self.gpg.sign_file(
                msg_path,
                keyid=fingerprint,
                passphrase=getattr(self, "passphrase", None),
                clearsign=False,
                detach=True,
                binary=False,
                output=sig_path,
                extra_args=["--armor"],
            )
            with open(sig_path, "rb") as f:
                return f.read()
        finally:
            for p in (msg_path, sig_path):
                if os.path.exists(p):
                    try:
                        os.unlink(p)
                    except OSError:
                        pass

    def encrypt_to(self, fingerprint: str, message: bytes) -> bytes:
        """Encrypt ``message`` to a recipient identified by fingerprint."""
        with tempfile.NamedTemporaryFile(
            delete=False, dir=self.homedir
        ) as mf:
            mf.write(message)
            msg_path = mf.name
        out_path = msg_path + ".asc"
        try:
            self.gpg.encrypt(
                msg_path,
                recipients=[fingerprint],
                output=out_path,
                armor=True,
                always_trust=True,
            )
            with open(out_path, "rb") as f:
                return f.read()
        finally:
            for p in (msg_path, out_path):
                if os.path.exists(p):
                    try:
                        os.unlink(p)
                    except OSError:
                        pass

    def cleanup(self) -> None:
        with contextlib.suppress(Exception):
            shutil.rmtree(self.homedir)


@contextlib.contextmanager
def gnupg_isolated():
    """Context-managed isolated GnuPG homedir for tests."""
    kr = GnupgKeyRing()
    try:
        yield kr
    finally:
        kr.cleanup()


async def create_user_post(email: str, password: str) -> dict[str, Any]:
    response: Response = await client.post(
        url="/auth/register",
        json={
            "email": email,
            "password": password,
            "is_active": True,
            "is_superuser": False,
            "is_verified": False,
        },
    )

    assert response.status_code == 201 or response.status_code == 400

    data_json: dict[str, str] = response.json()

    logger_obj.debug(f"User been created {data_json}")

    return data_json


def generate_login_headers(login_answer: dict[str, Any]) -> dict[str, str]:
    return {"Authorization": f"Bearer {login_answer['access_token']}"}


async def login_post(email: str, password: str) -> dict[str, Any]:
    response: Response = await client.post(
        url="/auth/login",
        headers={
            "Content-Type": "application/x-www-form-urlencoded",
        },
        content=f"grant_type=password&username={email}&password={password}&scope=&client_id=string&client_secret=string".encode(),
    )

    assert response.status_code == 200

    return response.json()


async def get_me(auth: dict[str, str]) -> dict[str, Any]:
    response: Response = await client.get(url="/users/me", headers=auth)

    assert response.status_code == 200

    return response.json()


async def change_user_public_key_post(
    auth: dict[str, str], public_key: bytes
) -> dict[str, Any]:
    """Upload an ASCII-armored PGP public key to /auth/change-public-key.

    ``public_key`` is the bytes produced by :meth:`GnupgKeyRing.export_public`.
    """
    login_headers: dict[str, str] = generate_login_headers(auth)
    response: Response = await client.post(
        url="/auth/change-public-key",
        headers={
            "accept": "application/json",
        }
        | login_headers,
        files={"new_public_key": ("key.asc", public_key, "text/plain")},
    )

    assert response.status_code == 200

    return response.json()


def generate_pgp_keys(email: str, user: str) -> tuple[bytes, bytes]:
    """Generate an RSA keypair via GnuPG in an isolated homedir.

    Returns ``(private_armored, public_armored)`` as bytes. Private
    key is kept for test signing; only the public key is uploaded to
    the server.

    Использует :class:`GnupgKeyRing` чтобы изолировать сгенерированный
    ключ от системного keyring.
    """
    kr = GnupgKeyRing()
    try:
        fingerprint = kr.generate(name=f"Test {user}", email=email)
        private = kr.export_private(fingerprint)
        public = kr.export_public(fingerprint)
        # Store fingerprint and homedir pointer in the private key
        # bytes via a sentinel — we need to know the fingerprint to sign later.
        # Caller is expected to also keep a reference to ``kr`` if signing.
        # For backward compatibility we return just the key bytes; helpers
        # accept ``fingerprint`` separately.
        global _PGP_KEY_REGISTRY
        _PGP_KEY_REGISTRY[user] = (kr, fingerprint)
        return private, public
    except Exception:
        kr.cleanup()
        raise


_PGP_KEY_REGISTRY: dict[str, tuple[GnupgKeyRing, str]] = {}


def get_pgp_keyring(user: str) -> GnupgKeyRing:
    """Return the isolated GnuPG keyring for a generated test user."""
    return _PGP_KEY_REGISTRY[user][0]


def get_pgp_fingerprint(user: str) -> str:
    return _PGP_KEY_REGISTRY[user][1]


def pgp_sign(user: str, message: bytes) -> bytes:
    """Detach-sign ``message`` using the generated private key for ``user``."""
    kr, fingerprint = _PGP_KEY_REGISTRY[user]
    return kr.sign_detached(fingerprint, message)


def pgp_encrypt(user: str, recipient_email: str, message: bytes) -> bytes:
    """Encrypt ``message`` for the recipient's public key.

    Uses the recipient's fingerprint resolved from the registry by email.
    """
    kr = _PGP_KEY_REGISTRY[user]
    # We need a fingerprint; look up by recipient_email in our registry
    for u, (_k, fp) in _PGP_KEY_REGISTRY.items():
        if u in recipient_email or recipient_email in u:
            return _k.encrypt_to(fp, message)
    raise RuntimeError(
        f"No PGP fingerprint registered for recipient {recipient_email}; "
        f"known users: {list(_PGP_KEY_REGISTRY.keys())}"
    )


def cleanup_pgp_keys() -> None:
    """Remove all generated test keys and cleanup isolated homedirs."""
    global _PGP_KEY_REGISTRY
    for _user, (kr, _fp) in _PGP_KEY_REGISTRY.items():
        try:
            kr.cleanup()
        except Exception:  # pragma: no cover
            pass
    _PGP_KEY_REGISTRY = {}


class BasicAPI(metaclass=ABCMeta):
    pass


class SingletonMeta(type):
    _instances: ClassVar[dict[Any, object]] = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            instance = super().__call__(*args, **kwargs)
            cls._instances[cls] = instance
        return cls._instances[cls]

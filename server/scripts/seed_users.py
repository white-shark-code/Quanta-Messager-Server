"""Seed default users into a fresh database.

Usage (from project root):

    .venv/bin/python scripts/seed_users.py
    # or with explicit app dir if PYTHONPATH isn't set:
    PYTHONPATH=src .venv/bin/python scripts/seed_users.py
"""

import asyncio

from fastapi_users.db import SQLAlchemyUserDatabase  # noqa: F401  must be first: warms up fastapi_users.db before messages.models triggers the circular import path

import messages.models  # noqa: F401  needed so SQLAlchemy resolves User.groups -> GroupChat
from authentication.models import User
from authentication.schemas import UserCreate
from authentication.services import UserManager
from database import _get_session_maker


DEFAULT_USERS: list[dict[str, str]] = [
    {
        "email": "alice@example.com",
        "password": "Password123!",
        "is_superuser": "false",
        "is_verified": "true",
    },
    {
        "email": "bob@example.com",
        "password": "Password123!",
        "is_superuser": "false",
        "is_verified": "true",
    },
    {
        "email": "carol@example.com",
        "password": "Password123!",
        "is_superuser": "false",
        "is_verified": "true",
    },
]


async def _create_one(manager: UserManager, payload: dict[str, str]) -> User:
    user_create = UserCreate(
        email=payload["email"],
        password=payload["password"],
        is_superuser=payload["is_superuser"] == "true",
        is_verified=payload["is_verified"] == "true",
    )
    return await manager.create(user_create)


async def main() -> None:
    session_maker = _get_session_maker()
    created: list[User] = []
    async with session_maker() as session:
        user_db = SQLAlchemyUserDatabase(session, User)
        manager = UserManager(user_db)
        for payload in DEFAULT_USERS:
            user = await _create_one(manager, payload)
            created.append(user)
        await session.commit()

    print(f"Created {len(created)} users:")
    for user in created:
        print(f"  - {user.email}  id={user.id}")


if __name__ == "__main__":
    asyncio.run(main())

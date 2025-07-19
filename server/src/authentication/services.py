from uuid import UUID

from fastapi import Depends, Request
from fastapi_users import BaseUserManager, FastAPIUsers, UUIDIDMixin
from fastapi_users.authentication import AuthenticationBackend, BearerTransport
from fastapi_users.authentication.strategy.db import (
    AccessTokenDatabase,
    DatabaseStrategy,
)
from fastapi_users.db import SQLAlchemyUserDatabase
from fastapi_users_db_sqlalchemy.access_token import SQLAlchemyAccessTokenDatabase
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_async_session
from settings import cfg

from .models import AccessToken, User


class UserManager(UUIDIDMixin, BaseUserManager[User, UUID]):
    reset_password_token_secret = cfg.SECRET_KEY_REST
    verification_token_secret = cfg.SECRET_KEY_VER

    async def on_after_register(self, user: User, request: Request | None = None):
        print(f"User {user.id} has registered.")

    async def on_after_forgot_password(
        self, user: User, token: str, request: Request | None = None
    ):
        print(f"User {user.id} has forgot their password. Reset token: {token}")

    async def on_after_request_verify(
        self, user: User, token: str, request: Request | None = None
    ):
        print(f"Verification requested for user {user.id}. Verification token: {token}")


async def get_user_db(
    session: AsyncSession = Depends(get_async_session),
) -> SQLAlchemyUserDatabase:
    """Service generator for getting user.

    Args:
        session (AsyncSession): session with open database connection

    """
    yield SQLAlchemyUserDatabase(session, User)


async def get_user_manager(user_db=Depends(get_user_db)):
    yield UserManager(user_db)


async def get_access_token_db(
    session: AsyncSession = Depends(get_async_session),
) -> SQLAlchemyAccessTokenDatabase:
    """Service generator for getting access token.

    Args:
        session (AsyncSession): session with open database connection

    """
    yield SQLAlchemyAccessTokenDatabase(session, AccessToken)


def get_database_strategy(
    access_token_db: AccessTokenDatabase[AccessToken] = Depends(get_access_token_db),
) -> DatabaseStrategy:
    """Service generator for getting manipulator with access token.

    Args:
        session (AsyncSession): session with open database connection

    """
    return DatabaseStrategy(access_token_db, lifetime_seconds=3600)


bearer_transport: BearerTransport = BearerTransport(tokenUrl="auth/login")

auth_backend: AuthenticationBackend = AuthenticationBackend(
    name="auth",
    transport=bearer_transport,
    get_strategy=get_database_strategy,
)

fastapi_users = FastAPIUsers[User, UUID](
    get_user_manager,
    [auth_backend],
)

current_user_av: callable = fastapi_users.current_user(
    active = True,
    verified = True if not cfg.DEBUG else False
)

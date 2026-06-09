"""Authentication services for user management and token handling.

This module provides the UserManager class, database access generators,
and authentication backend configuration for FastAPI Users.

Сервисы аутентификации для управления пользователями и токенами.

Модуль предоставляет класс UserManager, генераторы доступа к базе данных
и конфигурацию бэкенда аутентификации для FastAPI Users.
"""

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
    """Manager for user-related operations like registration and password reset.

    Менеджер для операций, связанных с пользователями: регистрация, сброс пароля.
    """

    reset_password_token_secret = cfg.SECRET_KEY_REST
    verification_token_secret = cfg.SECRET_KEY_VER

    async def on_after_register(self, user: User, request: Request | None = None):
        """Callback executed after a user registers.

        Обратный вызов, выполняемый после регистрации пользователя.

        Args:
            user: The newly registered user.
            request: The HTTP request object.
        """
        print(f"User {user.id} has registered.")

    async def on_after_forgot_password(
        self, user: User, token: str, request: Request | None = None
    ):
        """Callback executed after a password reset request.

        Обратный вызов, выполняемый после запроса сброса пароля.

        Args:
            user: The user who requested the reset.
            token: The reset token.
            request: The HTTP request object.
        """
        print(f"User {user.id} has forgot their password. Reset token: {token}")

    async def on_after_request_verify(
        self, user: User, token: str, request: Request | None = None
    ):
        """Callback executed after an email verification request.

        Обратный вызов, выполняемый после запроса верификации email.

        Args:
            user: The user being verified.
            token: The verification token.
            request: The HTTP request object.
        """
        print(f"Verification requested for user {user.id}. Verification token: {token}")


async def get_user_db(
    session: AsyncSession = Depends(get_async_session),
):
    """Dependency generator for user database access.

    Генератор зависимости для доступа к базе данных пользователей.

    Args:
        session: Async database session.

    Yields:
        SQLAlchemyUserDatabase instance.
    """
    yield SQLAlchemyUserDatabase(session, User)


async def get_user_manager(user_db=Depends(get_user_db)):
    """Dependency generator for user manager.

    Генератор зависимости для менеджера пользователей.

    Args:
        user_db: User database instance.

    Yields:
        UserManager instance.
    """
    yield UserManager(user_db)


async def get_access_token_db(
    session: AsyncSession = Depends(get_async_session),
):
    """Dependency generator for access token database access.

    Генератор зависимости для доступа к базе данных токенов.

    Args:
        session: Async database session.

    Yields:
        SQLAlchemyAccessTokenDatabase instance.
    """
    yield SQLAlchemyAccessTokenDatabase(session, AccessToken)


def get_database_strategy(
    access_token_db: AccessTokenDatabase[AccessToken] = Depends(get_access_token_db),
) -> DatabaseStrategy:
    """Dependency generator for database authentication strategy.

    Генератор зависимости для стратегии аутентификации через базу данных.

    Args:
        access_token_db: Access token database instance.

    Returns:
        DatabaseStrategy with configured token lifetime.
    """
    return DatabaseStrategy(access_token_db, lifetime_seconds=3600)


bearer_transport: BearerTransport = BearerTransport(tokenUrl="auth/login")

auth_backend: AuthenticationBackend = AuthenticationBackend(
    name="auth",
    transport=bearer_transport,
    get_strategy=get_database_strategy,
)

fastapi_users: FastAPIUsers = FastAPIUsers[User, UUID](
    get_user_manager,
    [auth_backend],
)

current_user_av: callable = fastapi_users.current_user(
    active=True, verified=True if not cfg.DEBUG else False
)

"""Integration conftest: DB engine, per-test rollback, dep override.

Integration conftest: движок БД, per-test-откат транзакции,
переопределение get_async_session для FastAPI.

Схема работы:
- apply_migrations (sync, session, autouse) — один раз на сессию делает
  `alembic upgrade head` через subprocess (alembic сам зовёт asyncio.run,
  поэтому не вызывается из-под pytest-asyncio event loop).
- engine (async, session, loop_scope=session) — AsyncEngine с NullPool.
  NullPool обязателен: пул держит соединения, привязанные к event loop,
  а pytest-asyncio при смене loop-а делает их «висячими».
- session_maker (async, session, loop_scope=session) — фабрика сессий.
- seed_users (async, session, autouse, loop_scope=session) — отдельная
  сессия + явный commit, чтобы зарегистрированные пользователи
  пережили per-test rollback.
- db_session (async, function, loop_scope=session) — свежая сессия
  внутри транзакции; на teardown — rollback, изолирующий тесты.
- override_get_async_session (async, function, autouse, loop_scope=session)
  — эндпоинты FastAPI получают ровно ту же сессию, что и db_session.
"""

import subprocess
import sys
from collections.abc import AsyncGenerator
from pathlib import Path

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import AsyncAdaptedQueuePool

from src.database import get_async_session
from src.main import app
from src.settings import cfg

from ..services import (
    change_user_public_key_post,
    create_user_post,
    generate_login_headers,
    login_post,
)


ROOT: Path = Path(__file__).resolve().parents[2]


@pytest.fixture(scope="session", autouse=True)
def apply_migrations() -> None:
    """alembic upgrade head — sync subprocess, до старта event loop."""
    subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "head"],
        cwd=ROOT,
        check=True,
    )


@pytest_asyncio.fixture(scope="session", loop_scope="session")
async def engine() -> AsyncGenerator[AsyncEngine, None]:
    """AsyncEngine с отключённым pool_reset_on_return.

    Дефолтный pool reset-on-return делает ROLLBACK каждый раз,
    когда connection возвращается в пул (между flush и следующим
    SELECT-ом). Это убивает INSERT без явного commit. Здесь
    отключаем reset-on-return, чтобы транзакция жила, сколько
    нам нужно, и закрытие тестовой сессии через session.begin/
    .rollback обеспечивает изоляцию.
    """
    eng: AsyncEngine = create_async_engine(
        url=cfg.DATABASE_URL,
        poolclass=AsyncAdaptedQueuePool,
        pool_size=1,
        max_overflow=0,
        pool_reset_on_return=None,
    )
    try:
        yield eng
    finally:
        await eng.dispose()


@pytest_asyncio.fixture(scope="session", loop_scope="session")
async def session_maker(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    """Фабрика сессий. expire_on_commit=False — иначе объекты «протухают»
    после commit-а в seed_users."""
    return async_sessionmaker(
        bind=engine,
        expire_on_commit=False,
        autoflush=False,
    )


@pytest_asyncio.fixture(scope="session", autouse=True, loop_scope="session")
async def seed_users(
    session_maker: async_sessionmaker[AsyncSession],
    users: list[dict[str, str]],
    gpg_keys: dict,
) -> None:
    """Регистрация пользователей через HTTP + явный commit.

    Используется отдельная сессия из session_maker; ни в коем случае
    не та же, что db_session, иначе commit затрётся rollback-ом теста.
    """
    async with session_maker() as session:

        async def _override() -> AsyncGenerator[AsyncSession, None]:
            yield session

        app.dependency_overrides[get_async_session] = _override
        try:
            await create_user_post(users[0]["email"], users[0]["password"])
            await create_user_post(users[1]["email"], users[1]["password"])

            auth0: dict = await login_post(
                users[0]["email"], users[0]["password"]
            )
            auth1: dict = await login_post(
                users[1]["email"], users[1]["password"]
            )

            await change_user_public_key_post(
                auth=auth0,
                public_key=gpg_keys[users[0]["email"]]["public"],
            )
            await change_user_public_key_post(
                auth=auth1,
                public_key=gpg_keys[users[1]["email"]]["public"],
            )

            await session.commit()
        finally:
            app.dependency_overrides.pop(get_async_session, None)


@pytest_asyncio.fixture(loop_scope="session")
async def db_session(
    session_maker: async_sessionmaker[AsyncSession],
) -> AsyncGenerator[AsyncSession, None]:
    """Сессия с явной транзакцией; rollback на teardown изолирует тест.

    AsyncSession + QueuePool + явный session.begin() держат одну
    транзакцию на все SQL-ы теста (INSERT и SELECT видят друг
    друга). На выходе из yield rollback откатывает все изменения
    этого теста.
    """
    async with session_maker() as session:
        await session.begin()
        try:
            yield session
        finally:
            await session.rollback()


@pytest_asyncio.fixture(autouse=True, loop_scope="session")
async def clean_db_before_test(
    session_maker: async_sessionmaker[AsyncSession],
) -> AsyncGenerator[None, None]:
    """TRUNCATE всех «тестовых» таблиц перед каждым тестом.

    Поскольку внутри тестов INSERT-ы коммитятся (commit в _post
    DialogChatRepo), rollback на teardown не откатывает данные.
    TRUNCATE-менее-элегантно, но эффективно: чистим таблицы чатов
    и сообщений перед каждым тестом. Таблицы user/accesstoken НЕ
    чистим — их заполняет seed_users один раз за сессию.

    Имена таблиц берём из Base.metadata, импортированного через
    `authentication.models`, поскольку из-за отсутствия src/__init__.py
    `from src.database import Base` и `from database import Base`
    дают разные Base с разным metadata.
    """
    from sqlalchemy import text

    import authentication.models  # noqa: F401  загружает модели
    from database import Base  # top-level импорт, корректный metadata

    keep_tables: set[str] = {"user", "accesstoken", "user_groups"}
    table_names: list[str] = [
        name
        for name in Base.metadata.tables.keys()
        if name not in keep_tables
    ]
    quoted: list[str] = [f'"{name}"' for name in table_names]
    async with session_maker() as session:
        await session.execute(
            text(
                "TRUNCATE TABLE "
                + ", ".join(quoted)
                + " RESTART IDENTITY CASCADE"
            )
        )
        await session.commit()
    yield


@pytest_asyncio.fixture(autouse=True, loop_scope="session")
async def override_get_async_session(
    db_session: AsyncSession,
) -> AsyncGenerator[None, None]:
    """FastAPI-эндпоинты используют ту же сессию, что и db_session.

    В finally делаем commit, чтобы INSERT-ы через базовый _post
    (без явного commit) тоже были видны следующим запросам.
    Изоляция тестов обеспечивается TRUNCATE перед каждым тестом.
    """

    async def _override() -> AsyncGenerator[AsyncSession, None]:
        yield db_session

    app.dependency_overrides[get_async_session] = _override
    try:
        yield
    finally:
        try:
            await db_session.commit()
        except Exception:
            await db_session.rollback()
        app.dependency_overrides.pop(get_async_session, None)


@pytest_asyncio.fixture(scope="session", loop_scope="session")
async def login() -> dict[str, str]:
    """Bearer-headers залогиненного user0."""
    data: dict = await login_post(email="user0@none.io", password="1234")
    return generate_login_headers(data)

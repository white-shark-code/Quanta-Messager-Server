"""Application settings loaded from environment variables.

This module defines configuration classes for database connection,
debug mode, and cryptographic secrets using pydantic-settings.

Настройки приложения, загружаемые из переменных окружения.

Модуль определяет классы конфигурации для подключения к базе данных,
режима отладки и криптографических секретов с использованием pydantic-settings.
"""

import os
from enum import Enum

from dotenv import dotenv_values
from pydantic_settings import BaseSettings


class DatabaseType(Enum):
    """Supported database types.

    Поддерживаемые типы баз данных.
    """

    POSTGRESQL = "postgresql"
    SQLITE = "sqlite"
    MYSQL = "mysql"
    MARIADB = "mariadb"

    @property
    def driver(self):
        """Return the async driver URL for this database type.

        Возвращает URL асинхронного драйвера для данного типа базы данных.
        """
        driver_dict: dict[str, str] = {
            "postgresql": "postgresql+asyncpg",
            "sqlite": "sqlite+aiosqlite",
            "mysql": "mysql+aiomysql",
            "mariadb": "mariadb+asyncmy",
        }

        return driver_dict.get(self.value)


def _load_env_values() -> dict[str, str]:
    """Load env values merging `.env.tests` and `.env` files.

    Загружает значения, сливая `.env.tests` и `.env`: tracked defaults
    first, then the gitignored local `.env` overrides them. Real process
    variables override both via `_resolve_values`.
    """
    from pathlib import Path

    current = Path.cwd()
    for _ in range(5):
        merged: dict[str, str] = {}
        env_test_path = current / ".env.tests"
        if env_test_path.exists():
            merged.update(
                {
                    k: v
                    for k, v in dotenv_values(env_test_path).items()
                    if v is not None
                }
            )
        env_path = current / ".env"
        if env_path.exists():
            merged.update(
                {k: v for k, v in dotenv_values(env_path).items() if v is not None}
            )
        if merged:
            return merged
        current = current.parent
    return {}


_env_values = _load_env_values()


def _resolve_values(file_values: dict[str, str] | None = None) -> dict[str, str]:
    """Merge file values with process environment (environment wins).

    Real process variables override `.env.tests`/`.env` file values, so
    `REDIS_URL=... uvicorn ...`, docker `environment:` and CI secrets
    always take effect no matter which env file exists. Empty/blank
    values are ignored (treated as unset).

    Объединяет файловые значения с переменными процесса (процесс важнее).
    """
    base = file_values if file_values is not None else _env_values
    override = {
        key: value
        for key, value in os.environ.items()
        if key in MainCFG.model_fields and value.strip()
    }
    return {**base, **override}


class MainCFG(BaseSettings):
    """Main application configuration.

    Основная конфигурация приложения.
    """

    model_config = {"env_file": None}

    DEBUG: bool = True
    DB_TYPE: DatabaseType
    DB_PATH: str
    SECRET_KEY_VER: str
    SECRET_KEY_REST: str
    MAX_MEDIA_SIZE_BYTES: int = 52428800
    MEDIA_STORAGE_TYPE: str = "database"
    REDIS_URL: str = "redis://localhost:6379/0"
    VAPID_PUBLIC_KEY: str = ""
    VAPID_PRIVATE_KEY: str = ""
    VAPID_CLAIMS_SUB: str = ""

    @property
    def DATABASE_URL(self):
        """Build the full database connection URL.

        Формирует полный URL подключения к базе данных.
        """
        url: str = f"{self.DB_TYPE.driver}://{self.DB_PATH}"
        if self.DB_TYPE == DatabaseType.SQLITE:
            url += "?check_same_thread=False"
        return url


cfg: MainCFG = MainCFG(**_resolve_values())

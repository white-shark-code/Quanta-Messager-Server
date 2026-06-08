"""Application settings loaded from environment variables.

This module defines configuration classes for database connection,
debug mode, and cryptographic secrets using pydantic-settings.

Настройки приложения, загружаемые из переменных окружения.

Модуль определяет классы конфигурации для подключения к базе данных,
режима отладки и криптографических секретов с использованием pydantic-settings.
"""

from enum import Enum

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
        driver_dict: dict[DatabaseType, str] = {
            "postgresql": "postgresql+asyncpg",
            "sqlite": "sqlite+aiosqlite",
            "mysql": "mysql+aiomysql",
            "mariadb": "mariadb+asyncmy",
        }

        return driver_dict.get(self.value)


class MainCFG(BaseSettings):
    """Main application configuration.

    Основная конфигурация приложения.
    """

    DEBUG: bool = True
    DB_TYPE: DatabaseType
    DB_PATH: str
    SECRET_KEY_VER: str
    SECRET_KEY_REST: str
    MAX_MEDIA_SIZE_BYTES: int = 52428800
    MEDIA_STORAGE_TYPE: str = "database"

    @property
    def DATABASE_URL(self):
        """Build the full database connection URL.

        Формирует полный URL подключения к базе данных.
        """
        url: str = f"{self.DB_TYPE.driver}://{self.DB_PATH}"
        if self.DB_TYPE == DatabaseType.SQLITE:
            url += "?check_same_thread=False"
        return url


cfg: MainCFG = MainCFG(_env_file="./.env")

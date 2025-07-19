from enum import Enum

from pydantic_settings import BaseSettings


class DatabaseType(Enum):
    POSTGRESQL: str = "postgresql"
    SQLITE: str = "sqlite"
    MYSQL: str = "mysql"
    MARIADB: str = "mariadb"

    @property
    def driver(self):
        driver_dict: dict[DatabaseType, str] = {
            "postgresql": "postgresql+asyncpg",
            "sqlite": "sqlite+aiosqlite",
            "mysql": "mysql+aiomysql",
            "mariadb": "mariadb+asyncmy",
        }

        return driver_dict.get(self.value)


class MainCFG(BaseSettings):
    DEBUG: bool = True
    DB_TYPE: DatabaseType
    DB_PATH: str
    SECRET_KEY_VER: str
    SECRET_KEY_REST: str

    @property
    def DATABASE_URL(self):
        url: str = f"{self.DB_TYPE.driver}://{self.DB_PATH}"
        if self.DB_TYPE == DatabaseType.SQLITE:
            url += "?check_same_thread=False"
        return url


cfg: MainCFG = MainCFG(_env_file='./.env')

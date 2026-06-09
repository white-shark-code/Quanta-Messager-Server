"""Abstract SQLAlchemy model base classes.

This module provides base ORM model classes with common column definitions
such as primary keys (int and UUID) and timestamp fields.
All concrete models should inherit from these base classes.

Базовые классы SQLAlchemy-моделей.

Модуль предоставляет базовые ORM-классы с общими определениями колонок,
такими как первичные ключи (int и UUID) и поля временных меток.
Все конкретные модели должны наследовать эти базовые классы.
"""

from datetime import datetime
from uuid import UUID, uuid4

from fastapi_users_db_sqlalchemy.generics import GUID
from sqlalchemy.orm import Mapped, mapped_column

from database import Base


class AbstractModel(Base):
    """Base abstract model without any columns.

    Set __abstract__ = True to prevent SQLAlchemy from creating a table.

    Базовая абстрактная модель без колонок.

    Установите __abstract__ = True, чтобы SQLAlchemy не создавал таблицу.
    """

    __abstract__ = True


class AbstractModelWithID(Base):
    """Base model with a generic primary key column.

    Subclasses must define the actual type and constraints of the id column.

    Базовая модель с обобщённым первичным ключом.

    Подклассы должны определить фактический тип и ограничения колонки id.
    """

    __abstract__ = True
    id = mapped_column(primary_key=True)


class AbstractModelWithCreateAt(Base):
    """Base model with a created_at timestamp column.

    Automatically sets the timestamp to UTC time on creation.

    Базовая модель с колонкой временной метки создания.

    Автоматически устанавливает временную метку в UTC при создании.
    """

    __abstract__ = True

    create_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, nullable=False)


class AbstractModelWithUUID(AbstractModelWithID):
    """Base model with a UUID primary key.

    Uses GUID type for cross-database UUID compatibility.

    Базовая модель с UUID первичным ключом.

    Использует тип GUID для кросс-базовой совместимости UUID.
    """

    __abstract__ = True

    id: Mapped[UUID] = mapped_column(GUID, primary_key=True, default=uuid4)


class AbstractModelWithIntID(AbstractModelWithID):
    """Base model with an integer primary key.

    Базовая модель с целочисленным первичным ключом.
    """

    __abstract__ = True

    id: Mapped[int] = mapped_column(primary_key=True)

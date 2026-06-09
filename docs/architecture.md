# Architecture / Архитектура

## Overview / Обзор

Quant is an encrypted messaging server built with FastAPI. It uses PGP encryption for end-to-end message security and supports both private (dialog) and group chats.

Quant — это зашифрованный сервер сообщений, построенный на FastAPI. Использует PGP-шифрование для сквозной защиты сообщений и поддерживает как приватные (диалоговые), так и групповые чаты.

---

## Project Structure / Структура проекта

```
server/src/
├── main.py                  # Application entry point / Точка входа приложения
├── database.py              # SQLAlchemy engines and sessions / Движки и сессии SQLAlchemy
├── settings.py              # Configuration from environment / Конфигурация из окружения
├── shared/                  # Shared abstractions / Общие абстракции
│   ├── abstract_repository.py    # Repository interfaces / Интерфейсы репозиториев
│   ├── abstract_facade.py        # Facade pattern base classes / Базовые классы фасадов
│   ├── abstract_schemas.py       # Pydantic base schemas / Базовые Pydantic-схемы
│   ├── abstract_sqlalchemy_models.py   # ORM base models / Базовые ORM-модели
│   ├── abstract_sqlalchemy_repository.py  # SQLAlchemy repo base / База SQLAlchemy-репозитория
│   ├── basic_repository.py   # Concrete SQLAlchemy repos / Конкретные SQLAlchemy-репозитории
│   ├── basic_schemas.py      # Concrete pagination schemas / Конкретные схемы пагинации
│   └── exceptions.py         # Custom exceptions / Пользовательские исключения
├── authentication/            # User auth and PGP keys / Аутентификация и PGP-ключи
│   ├── models.py             # User, AccessToken, UserGroup / Пользователь, токен, группа
│   ├── schemas.py            # Pydantic schemas for auth / Pydantic-схемы аутентификации
│   ├── services.py           # UserManager, auth backend / Менеджер пользователей, бэкенд
│   └── router.py             # PGP key management endpoint / Эндпоинт управления PGP-ключами
├── messages/                  # Chat and message handling / Обработка чатов и сообщений
│   ├── models.py             # DialogChat, GroupChat, messages, MediaAttachment, MediaBlobData / Чаты, сообщения, медиа
│   ├── schemas.py            # Request/response schemas / Схемы запросов/ответов
│   ├── repository.py         # Data access layer / Слой доступа к данным
│   ├── services.py           # PGP signature verification / Проверка PGP-подписей
│   ├── facade.py             # Business logic layer / Слой бизнес-логики
│   ├── storage.py            # Media storage abstraction (DB/S3) / Абстракция хранилища медиа
│   └── router.py             # REST endpoints / REST-эндпоинты
├── events/                    # Notification events / События уведомлений
│   ├── models.py             # EventInDialogChat, EventInGroupChat
│   ├── schemas.py            # Event schemas / Схемы событий
│   ├── services.py           # Event creation helpers / Помощники создания событий
│   └── router.py             # Event CRUD endpoints / Эндпоинты событий
└── alembic/                   # Database migrations / Миграции базы данных
```

---

## Architectural Patterns / Архитектурные паттерны

### Repository Pattern / Паттерн Repository

The repository layer abstracts database operations behind generic interfaces.

Слой репозиториев абстрагирует операции с базой данных за обобщёнными интерфейсами.

**Layer hierarchy / Иерархия слоёв:**

```
AbstractAsyncRepoCreate/Read/Update/Delete    # Operation mixins / Миксины операций
    ↓
AbstractAsyncCRUDRepo                          # Combination interfaces / Комбинированные интерфейсы
    ↓
AbstractDefaultSQLAlchemyAsyncRepository       # SQLAlchemy base / База SQLAlchemy
    ↓
AbstractDefaultSQLAlchemyCreate/Read/Update/Delete  # SQLAlchemy mixins / Миксины SQLAlchemy
    ↓
DialogChatRepo, DialogMessageRepo              # Concrete repos / Конкретные репозитории
```

Each repository class inherits from combination classes (e.g., `AbstractUUIDSQLAlchemyCRDP`) that bundle CRUD operations with pagination support.

Каждый класс репозитория наследуется от комбинированных классов (например, `AbstractUUIDSQLAlchemyCRDP`), которые объединяют CRUD-операции с поддержкой пагинации.

### Facade Pattern / Паттерн Facade

Facades wrap repositories and add business logic through pre/post processing hooks.

Фасады оборачивают репозитории и добавляют бизнес-логику через хуки предварительной и последующей обработки.

```
DialogFacade
├── _before_create() → validate user exists
├── _after_read()    → check access permissions
├── _before_delete() → verify ownership
└── delegates to DialogChatRepo for data access
```

### Template Method Pattern / Паттерн Template Method

Each repository operation follows a template:

Каждая операция репозитория следует шаблону:

```python
async def post(schema):
    await self._before_post()      # Hook / Хук
    result = await self._post()    # Abstract method / Абстрактный метод
    return self._output_pyd_model.model_validate(result)  # Validation / Валидация
```

---

## Data Flow / Поток данных

```
HTTP Request
    ↓
Router (FastAPI endpoint)
    ↓
Facade (business logic + hooks)
    ↓
Repository (data access)
    ↓
SQLAlchemy → Database
    ↓
Pydantic validation
    ↓
HTTP Response
```

---

## Authentication / Аутентификация

Uses `fastapi-users` with database-backed JWT tokens.

Использует `fastapi-users` с JWT-токенами на основе базы данных.

- **Bearer token transport** — tokens stored in `access_tokens` table
- **User roles** — `reader`, `user`, `keyman`, `moderator`, `small_admin`, `admin`
- **PGP public keys** — stored in `user.public_key` for message encryption

---

## Encryption / Шифрование

- **PGP (Pretty Good Privacy)** — end-to-end message encryption
- **Message signing** — each message includes a digital signature
- **Server never sees plaintext** — messages are encrypted client-side before transmission

- **PGP (Pretty Good Privacy)** — сквозное шифрование сообщений
- **Подписывание сообщений** — каждое сообщение включает цифровую подпись
- **Сервер никогда не видит открытый текст** — сообщения шифруются на клиенте перед отправкой

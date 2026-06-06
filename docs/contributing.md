# Contributing Guide / Гайд для контрибьюторов

## Getting Started / Начало работы

### Prerequisites / Требования

- Python 3.13+
- PostgreSQL, SQLite, MySQL, or MariaDB
- PGP key pair (for testing)

### Setup / Настройка

```bash
# Clone the repository / Клонируйте репозиторий
git clone <repository-url>
cd Quant/server

# Create virtual environment / Создайте виртуальное окружение
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
.venv\Scripts\activate     # Windows

# Install dependencies / Установите зависимости
pip install -e ".[postgresql]"  # or [sqlite], [mysql], [mariadb]

# Copy and configure environment / Скопируйте и настройте окружение
cp .env_example .env
# Edit .env with your database URL and secrets / Отредактируйте .env
```

---

## Project Structure / Структура проекта

See [architecture.md](architecture.md) for a detailed overview.

Подробный обзор см. в [architecture.md](architecture.md).

---

## Coding Standards / Стандарты кода

### Docstrings / Документация

All public classes, methods, and functions must have **bilingual docstrings** (English first, then Russian):

Все публичные классы, методы и функции должны иметь **двуязычные docstring'и** (сначала английский, затем русский):

```python
def my_function(arg: str) -> int:
    """Short description in English.

    Краткое описание на русском.

    Args:
        arg: Description / Описание

    Returns:
        Description / Описание
    """
    pass
```

### Type Hints / Аннотации типов

All function signatures must include type hints:

Все сигнатуры функций должны включать аннотации типов:

```python
async def get_user(self, user_id: UUID) -> User | None:
    ...
```

### Code Style / Стиль кода

- Use `ruff` for linting: `ruff check server/src/`
- Max line length: 88 characters
- Follow Google-style docstrings

---

## Development Workflow / Рабочий процесс разработки

### 1. Create a branch / Создайте ветку

```bash
git checkout -b feature/my-feature
```

### 2. Make changes / Внесите изменения

Follow the existing patterns:

Следуйте существующим паттернам:

- **Repository layer** — data access only, no business logic
- **Facade layer** — business logic in `_before_*` and `_after_*` hooks
- **Router layer** — HTTP endpoints, dependency injection, error handling

### 3. Run tests / Запустите тесты

```bash
pytest tests/
```

### 4. Run linter / Запустите линтер

```bash
server/.venv/bin/ruff check server/src/
server/.venv/bin/ruff check server/src/ --fix  # Auto-fix where possible
```

### 5. Commit / Закоммитьте

```bash
git add .
git commit -m "feat: add new feature"
```

---

## Adding a New Feature / Добавление новой функции

### Example: Adding a new entity / Пример: добавление новой сущности

1. **Model** — Create SQLAlchemy model in `models.py`
2. **Schema** — Create Pydantic schemas in `schemas.py`
3. **Repository** — Create repo class inheriting from `AbstractUUIDSQLAlchemyCRUD*`
4. **Facade** — Create facade with business logic hooks
5. **Router** — Add endpoints
6. **Docs** — Update `api.md` and `architecture.md`

---

## Pull Request Process / Процесс Pull Request

1. Ensure all tests pass / Убедитесь, что все тесты проходят
2. Ensure ruff passes with no errors / Убедитесь, что ruff не выдаёт ошибок
3. Update documentation if needed / Обновите документацию при необходимости
4. Request review from a maintainer / Запросите ревью от мейнтейнера

### PR Title Format / Формат заголовка PR

```
type: short description
```

Types: `feat`, `fix`, `docs`, `refactor`, `test`, `chore`

---

## Questions? / Вопросы?

- Check [architecture.md](architecture.md) for design patterns
- Check [api.md](api.md) for API details
- Check [security.md](security.md) for security guidelines

- Проверьте [architecture.md](architecture.md) для паттернов проектирования
- Проверьте [api.md](api.md) для деталей API
- Проверьте [security.md](security.md) для рекомендаций по безопасности

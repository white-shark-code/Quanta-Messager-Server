# Backend image: FastAPI + uvicorn, deps via uv, migrations on startup.
# No secrets inside: all config comes from environment at runtime.
FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    PATH="/app/.venv/bin:$PATH"

WORKDIR /app

# Install uv (official Astral binary)
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Dependencies first for better layer caching (incl. postgresql + sqlite extras)
COPY pyproject.toml uv.lock ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --extra postgresql --extra sqlite --no-dev

# Runtime sources only (.env / tests / caches stay out via .dockerignore)
COPY alembic.ini ./
COPY src ./src

EXPOSE 8000

# Flat imports (run from /app): migrate, then serve
CMD ["sh", "-c", "uv run --frozen alembic upgrade head && uv run --frozen uvicorn main:app --app-dir src --host 0.0.0.0 --port 8000"]

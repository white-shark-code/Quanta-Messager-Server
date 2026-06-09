"""FastAPI application entry point.

This module creates the FastAPI application instance,
configures authentication and messaging routers, and sets up
the OpenAPI documentation.

Точка входа FastAPI-приложения.

Модуль создаёт экземпляр FastAPI-приложения, настраивает роутеры
аутентификации и сообщений, а также конфигурирует документацию OpenAPI.
"""

"""FastAPI application entry point.

This module creates the FastAPI application instance,
configures authentication and messaging routers, and sets up
the OpenAPI documentation.

Точка входа FastAPI-приложения.

Модуль создаёт экземпляр FastAPI-приложения, настраивает роутеры
аутентификации и сообщений, а также конфигурирует документацию OpenAPI.
"""

from fastapi import FastAPI

from authentication.router import auth_router
from authentication.schemas import UserCreate, UserRead
from authentication.services import auth_backend, fastapi_users
from events.router import events
from messages.router import group_chats, group_messages, private_chats, private_messages
from settings import cfg

app: FastAPI = FastAPI(debug=cfg.DEBUG, title="Quant messaging server", version="0.0.7")

# FastAPI Users routers

app.include_router(
    fastapi_users.get_auth_router(auth_backend),
    prefix="/auth",
    tags=["auth"],
)

app.include_router(
    fastapi_users.get_register_router(UserRead, UserCreate),
    prefix="/auth",
    tags=["auth"],
)

app.include_router(
    fastapi_users.get_verify_router(UserRead),
    prefix="/auth",
    tags=["auth"],
)

app.include_router(
    fastapi_users.get_reset_password_router(),
    prefix="/auth",
    tags=["auth"],
)

app.include_router(
    auth_router,
    prefix="/auth",
    tags=["auth"],
)

# Messaging routers

app.include_router(prefix="/messages", router=private_chats, tags=["messages"])

app.include_router(prefix="/messages", router=private_messages, tags=["messages"])

# Group routers

app.include_router(prefix="/group-messages", router=group_chats, tags=["messages"])

app.include_router(prefix="/group-messages", router=group_messages, tags=["messages"])

# Events router

app.include_router(router=events, tags=["events"])

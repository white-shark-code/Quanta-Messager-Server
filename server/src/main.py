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

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from authentication.router import auth_router
from authentication.schemas import UserCreate, UserRead, UserUpdate
from authentication.services import auth_backend, fastapi_users
from events.router import events
from messages.router import group_chats, group_messages, private_chats, private_messages
from settings import cfg
from shared.exceptions import AppException
from users.router import router as users_router

app: FastAPI = FastAPI(debug=cfg.DEBUG, title="Quant messaging server", version="0.0.7")


@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    """Convert domain AppException into a JSON HTTP response.

    Translates domain exceptions (e.g., ChatAccessDeniedException,
    UserNotFoundException) into proper HTTP responses with the matching
    status code and a user-facing message, so endpoints don't crash
    with HTTP 500.

    Преобразует доменные AppException в JSON-ответ с корректным кодом.
    """
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.user_message},
    )

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
    fastapi_users.get_users_router(UserRead, user_update_schema=UserUpdate),
    prefix="/users",
    tags=["users"],
)

app.include_router(users_router)

# CORS: Tauri WebView runs on tauri://localhost (or http://tauri.localhost on
# newer Tauri). Without this middleware, the browser blocks cross-origin
# fetch() calls from the frontend to this API. Allow Vite dev origin too.
# CORS: Tauri WebView работает на tauri://localhost (или http://tauri.localhost
# в новых Tauri). Без этого middleware браузер блокирует cross-origin запросы
# фронтенда к этому API. Также разрешаем dev-origin Vite.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "tauri://localhost",
        "http://tauri.localhost",
        "http://localhost:1420",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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

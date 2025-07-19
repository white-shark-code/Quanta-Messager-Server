from fastapi import FastAPI

from authentication.router import auth_router
from authentication.schemas import UserCreate, UserRead, UserUpdate
from authentication.services import auth_backend, fastapi_users
from messages.router import private_chats, private_messages
from settings import cfg

app: FastAPI = FastAPI(
    debug=cfg.DEBUG,
    title="Quant messaging server",
    version='0.0.5'
)

# FastAPI Users routers

app.include_router(
    fastapi_users.get_auth_router(auth_backend),
    prefix='/auth',
    tags=['auth'],
)

app.include_router(
    fastapi_users.get_register_router(UserRead, UserCreate),
    prefix='/auth',
    tags=['auth'],
)

app.include_router(
    fastapi_users.get_verify_router(UserRead),
    prefix='/auth',
    tags=['auth'],
)

app.include_router(
    fastapi_users.get_reset_password_router(),
    prefix='/auth',
    tags=['auth'],
)

app.include_router(
    fastapi_users.get_users_router(UserRead, UserUpdate),
    prefix='/users',
    tags=['users'],
)

app.include_router(
    fastapi_users.get_users_router(UserRead, UserUpdate),
    prefix='/users',
    tags=['users'],
)

app.include_router(
    auth_router,
    prefix='/auth',
    tags=['auth'],
)

# Messaging routers

app.include_router(
    prefix='/messages',
    router=private_chats,
    tags=['messages']
)

app.include_router(
    prefix='/messages',
    router=private_messages,
    tags=['messages']
)

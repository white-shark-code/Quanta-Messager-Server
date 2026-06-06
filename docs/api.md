# API Reference / Справочник API

Base URL: `/`  
Interactive docs (Swagger): `/docs`  
ReDoc: `/redoc`

---

## Authentication / Аутентификация

### POST `/auth/login`
Login and receive a bearer token.

Войти и получить bearer-токен.

**Request / Запрос:**
```json
{
  "username": "string",
  "password": "string"
}
```

**Response / Ответ:**
```json
{
  "access_token": "string",
  "token_type": "bearer"
}
```

---

### POST `/auth/register`
Register a new user.

Зарегистрировать нового пользователя.

**Request / Запрос:**
```json
{
  "email": "user@example.com",
  "password": "string"
}
```

**Response / Ответ:** — `UserRead` schema

---

### POST `/auth/change-public-key`
Upload a new PGP public key for the authenticated user.

Загрузить новый PGP публичный ключ для аутентифицированного пользователя.

**Request / Запрос:** `multipart/form-data` with `new_public_key` file (text/plain, max 10KB)

**Response / Ответ:** — `UserReadWithPGP` schema

**Errors / Ошибки:**
- `400` — Invalid PGP data / Невалидные данные PGP
- `422` — File too large or not a public key / Файл слишком большой или не публичный ключ

---

## Private Chats / Приватные чаты

### GET `/private-chat/{chat_id}`
Get dialog chat information.

Получить информацию о диалоговом чате.

**Response / Ответ:** — `DefaultDialogChat`

---

### POST `/private-chat/`
Create a new dialog chat with another user.

Создать новый диалоговый чат с другим пользователем.

**Request / Запрос:**
```json
{
  "name": "string",
  "user": "uuid-of-other-user"
}
```

**Response / Ответ:** — `DefaultDialogChat`

---

### GET `/private-chats/`
Get all dialog chats for the current user.

Получить все диалоговые чаты текущего пользователя.

**Response / Ответ:** — `ListItems[DefaultDialogChat]`

---

### DELETE `/private-chat/{chat_id}/`
Delete a dialog chat.

Удалить диалоговый чат.

**Response / Ответ:** — `DefaultDialogChat`

---

## Private Messages / Приватные сообщения

### GET `/private-messages/{chat_id}`
Get all messages from a dialog chat.

Получить все сообщения из диалогового чата.

**Query params / Параметры запроса:** `offset`, `limit` (via pagination dependency)

**Response / Ответ:** — `ListItems[DialogMessage]`

---

### POST `/private-messages/{chat_id}`
Create a new encrypted message in a dialog chat.

Создать новое зашифрованное сообщение в диалоговом чате.

**Request / Запрос:**
```json
{
  "encrypted_message": "bytes",
  "signature": "bytes"
}
```

**Response / Ответ:** — `DialogMessage`

**Errors / Ошибки:**
- `404` — Chat not found or user not a participant / Чат не найден или пользователь не участник
- `405` — User has no public key / У пользователя нет публичного ключа
- `422` — Invalid signature or encryption / Невалидная подпись или шифрование

---

## Group Chats / Групповые чаты

### POST `/group-chat/`
Create a new group chat.

Создать новый групповой чат.

**Request / Запрос:**
```json
{
  "name": "string",
  "user": "uuid"
}
```

**Response / Ответ:** — `DefaultDialogChat`

---

### POST `/group-messages/{chat_id}`
Create a new encrypted message in a group chat.

Создать новое зашифрованное сообщение в групповом чате.

**Request / Запрос:**
```json
{
  "encrypted_message": "bytes",
  "signature": "bytes"
}
```

**Response / Ответ:** — `DialogMessage`

---

## Events / События

### GET `/event/dialogs/`
Get all unread dialog events for the current user.

Получить все непрочитанные события диалогов для текущего пользователя.

**Response / Ответ:** — `ListItems[EventInDialogChat]`

---

### GET `/event/groups/`
Get all unread group events for the current user.

Получить все непрочитанные события групп для текущего пользователя.

**Response / Ответ:** — `ListItems[EventInGroupChat]`

---

### POST `/event/dialog/readed/{event_id}`
Mark a dialog event as read (reset counter to 0).

Отметить событие диалога как прочитанное (сбросить счётчик до 0).

**Response / Ответ:** — `200 OK`

---

### POST `/event/group/readed/{event_id}`
Mark a group event as read (reset counter to 0).

Отметить событие группы как прочитанное (сбросить счётчик до 0).

**Response / Ответ:** — `200 OK`

---

## Schemas / Схемы

### `DefaultDialogChat`
```json
{
  "id": "uuid",
  "name": "string",
  "user0": "uuid",
  "user1": "uuid",
  "creation_datetime": "datetime"
}
```

### `DialogMessage`
```json
{
  "id": "uuid",
  "owner_id": "uuid",
  "encrypted_message": "bytes",
  "creation_datetime": "datetime",
  "chat_id": "uuid"
}
```

### `EventInDialogChat`
```json
{
  "id": "uuid",
  "chat_id": "uuid",
  "user_id": "uuid",
  "count": 0
}
```

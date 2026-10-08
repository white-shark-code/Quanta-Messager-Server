# Уведомления / Notifications

## RU

### WebSocket (`/event/ws`)

- Подключение: `GET /event/ws?token=<access_token>` — тот же Bearer-токен,
  что и для REST (fastapi-users, database strategy, lifetime 3600s).
  Токен передаётся в query, т.к. браузер не может ставить кастомные
  заголовки при WebSocket-handshake.
- Сокет сначала принимается (`accept`), затем проверяется токен.
  Без токена или с невалидным/протухшим/неактивным пользователем
  сервер закрывает соединение кодом **4401** (unauthorized).
  Клиент должен перелогиниться, взять свежий токен и переподключиться
  с backoff.
- Первое сообщение после успешной проверки:
  `{"type": "connected", "user_id": "<uuid>"}`.
- Типы пушей — только ID, без шифротекста и имён
  (клиент догружает данные через REST):
  - `{"type": "new_dialog_message", "chat_id": ..., "message_id": ...,
    "sender_id": ...}`
  - `{"type": "new_group_message", "chat_id": ..., "message_id": ...,
    "sender_id": ...}`
- Keepalive: клиент шлёт текст `ping`, сервер отвечает
  `{"type": "pong"}`.
- Один пользователь может держать несколько сокетов (UI + демон);
  `manager.send_to_user` рассылает сообщение на все сокеты пользователя.

### Web Push

- `GET /meta` (без аутентификации) → `{"vapid_public_key": "..."}`.
  Пустая строка означает, что VAPID не настроен и подписка невозможна.
- `POST /push/subscribe` (auth) — upsert подписки браузера.
  Тело: `{"endpoint": "<url>", "keys": {"p256dh": "...", "auth": "..."}}`.
  Ответ `{"endpoint": "<url>"}`: HTTP 201 — новая подписка,
  HTTP 200 — ключи существующего endpoint обновлены.
- `DELETE /push/unsubscribe` (auth) — удалить свою подписку, идемпотентно.
  Тело: `{"endpoint": "<url>"}`. Всегда HTTP 204, даже если подписки не было.
  Удалить можно только свою подписку.
- Push-payload содержит только ID (`type`, `chat_id`, `message_id`) —
  без имён и шифротекста, т.к. пуши идут через сторонние серверы.

### Redis-шина

- Канал: `events`. Redis **обязателен** — in-memory fallback нет.
- Конверт (JSON-строка):
  `{"recipients": ["<user_uuid>", ...], "payload": {...}}`.
- Публикация: `publish_event(recipients, payload)`.
- Каждый uvicorn-воркер держит один фоновый `subscriber`
  (старт/стоп в lifespan `main.py`), который декодирует конверт
  и вызывает локальный `manager.send_to_user` для каждого получателя.
  Так решается проблема «сокет живёт в другом процессе».
- Ошибки шины никогда не бросаются наружу — только debug-лог.

### Контракт доставки

- Доставка **best-effort**: `send_to_user` никогда не бросает исключение,
  мёртвые сокеты молча удаляются. Web Push тоже best-effort;
  протухшие endpoint (HTTP 410/404 от пуш-сервиса) удаляются из БД.
- Источник правды — REST-счётчики: `GET /event/dialogs/`,
  `GET /event/groups/` и `POST /event/dialog/readed/{id}`,
  `POST /event/group/readed/{id}`. Клиент обязан сверяться с ними
  при старте и после переподключения WS.
- Ограничение: без доступного Redis realtime-уведомления не работают
  (нужен `REDIS_URL`, см. `.env.example`).

## EN

### WebSocket (`/event/ws`)

- Connect: `GET /event/ws?token=<access_token>` — the same Bearer token
  as REST (fastapi-users, database strategy, 3600s lifetime).
  The token goes in the query string because browsers cannot set custom
  headers on the WebSocket handshake.
- The socket is accepted first, then the token is validated.
  With a missing/invalid/expired token (or inactive user) the server
  closes the connection with code **4401** (unauthorized).
  The client must re-login, take a fresh token and reconnect with backoff.
- First message after successful validation:
  `{"type": "connected", "user_id": "<uuid>"}`.
- Push types carry IDs only, no ciphertext or names
  (the client fetches data via REST):
  - `{"type": "new_dialog_message", "chat_id": ..., "message_id": ...,
    "sender_id": ...}`
  - `{"type": "new_group_message", "chat_id": ..., "message_id": ...,
    "sender_id": ...}`
- Keepalive: the client sends text `ping`, the server replies
  `{"type": "pong"}`.
- One user may hold several sockets (UI + daemon);
  `manager.send_to_user` fans out to all of the user's sockets.

### Web Push

- `GET /meta` (no auth) → `{"vapid_public_key": "..."}`.
  An empty string means VAPID is not configured and subscribing is impossible.
- `POST /push/subscribe` (auth) — upsert a browser subscription.
  Body: `{"endpoint": "<url>", "keys": {"p256dh": "...", "auth": "..."}}`.
  Response `{"endpoint": "<url>"}`: HTTP 201 — new subscription,
  HTTP 200 — keys of an existing endpoint refreshed.
- `DELETE /push/unsubscribe` (auth) — remove your own subscription,
  idempotent. Body: `{"endpoint": "<url>"}`. Always HTTP 204, even when
  nothing was subscribed. Only your own subscription can be removed.
- Push payloads carry IDs only (`type`, `chat_id`, `message_id`) —
  no names or ciphertext, because pushes travel via third-party servers.

### Redis bus

- Channel: `events`. Redis is **mandatory** — there is no in-memory fallback.
- Envelope (JSON string):
  `{"recipients": ["<user_uuid>", ...], "payload": {...}}`.
- Publishing: `publish_event(recipients, payload)`.
- Each uvicorn worker runs one background `subscriber`
  (started/stopped in the `main.py` lifespan) that decodes the envelope
  and calls the local `manager.send_to_user` for every recipient.
  This solves the "socket lives in another process" problem.
- Bus errors never propagate — debug log only.

### Delivery contract

- Delivery is **best-effort**: `send_to_user` never raises,
  dead sockets are silently evicted. Web Push is best-effort too;
  stale endpoints (HTTP 410/404 from the push service) are deleted from storage.
- Source of truth is the REST counters: `GET /event/dialogs/`,
  `GET /event/groups/` plus `POST /event/dialog/readed/{id}`,
  `POST /event/group/readed/{id}`. Clients must reconcile with them
  on startup and after every WS reconnect.
- Limitation: without a reachable Redis, realtime notifications do not work
  (`REDIS_URL` is required, see `.env.example`).

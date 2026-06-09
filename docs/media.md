# Media Support / Поддержка медиа

## Overview / Обзор

Quant supports client-side encrypted media attachments. All encryption and signing happens on the client. The server only verifies signatures and stores encrypted blobs.

Quant поддерживает медиа-вложения с шифрованием на клиенте. Всё шифрование и подписание происходит на клиенте. Сервер только проверяет подписи и хранит зашифрованные данные.

---

## Architecture / Архитектура

### Two-phase upload / Двухфазная загрузка

Медиа загружается отдельно от текста сообщения. Это позволяет:
- Показывать прогресс загрузки для каждого файла
- Загружать файлы параллельно
- Повторить загрузку при обрыве связи
- Не блокировать отправку текста

**Phase 1 — Upload media / Фаза 1 — Загрузка медиа:**
```
POST /private-message/{chat_id}/media/upload
→ { id: "media-uuid" }
```
Сервер проверяет подпись, сохраняет медиа как orphan (`message_id = NULL`).

**Phase 2 — Send message / Фаза 2 — Отправка сообщения:**
```
POST /private-message/{chat_id}
Body: { encrypted_message, signature, media_ids: ["media-uuid"] }
```
Сервер проверяет подпись текста, линкует медиа к сообщению.

---

## Database / База данных

### Table `media_attachments` (metadata / метаданные)

| Column | Type | Description |
|--------|------|-------------|
| `id` | UUID (PK) | Attachment identifier |
| `message_id` | UUID (FK, nullable) | Link to message. `NULL` = orphan |
| `mime_type` | VARCHAR(128) | MIME type (plaintext metadata) |
| `file_size` | INT | File size in bytes (plaintext metadata) |
| `signature` | BYTEA | PGP signature of encrypted file |
| `creation_datetime` | TIMESTAMP | Creation time |
| `owner_id` | UUID (FK → user) | File owner |

### Table `media_blob_data` (binary data / бинарные данные)

| Column | Type | Description |
|--------|------|-------------|
| `media_id` | UUID (PK, FK → media_attachments.id) | 1:1 link to media_attachments |
| `encrypted_file` | BYTEA | Encrypted file blob |

**Why separate tables / Почему отдельные таблицы:**
- Metadata is small, blob is large — different access patterns
- Future S3 migration: just remove row from `media_blob_data`, keep `media_attachments`
- Doesn't bloat the main messages table

---

## API Endpoints

### Upload media / Загрузка медиа

```
POST /private-message/{chat_id}/media/upload
POST /group-message/{chat_id}/media/upload
```

**Request body:**
```json
{
  "encrypted_file": "<base64 bytes>",
  "signature": "<base64 bytes>",
  "mime_type": "image/jpeg",
  "file_size": 245678
}
```

**Response (201):**
```json
{
  "id": "uuid-media-1",
  "mime_type": "image/jpeg",
  "file_size": 245678,
  "creation_datetime": "2026-06-08T12:00:00Z"
}
```

**Server logic / Логика сервера:**
1. Check `file_size <= MAX_MEDIA_SIZE_BYTES`
2. Verify signature: `check_media_signature(encrypted_file, signature, user.public_key)`
3. Create `media_attachments` row with `message_id = NULL`
4. Create `media_blob_data` row with encrypted blob
5. Return `id`

**Errors / Ошибки:**
- `413 Payload Too Large` — file exceeds limit
- `422 Unprocessable Entity` — invalid signature or not PGP

---

### Send message with media / Отправка сообщения с медиа

```
POST /private-message/{chat_id}
POST /group-message/{chat_id}
```

**Request body:**
```json
{
  "encrypted_message": "<base64 bytes>",
  "signature": "<base64 bytes>",
  "media_ids": ["uuid-media-1", "uuid-media-2"]
}
```

`media_ids` is optional.

**Server logic / Логика сервера:**
1. Verify text signature via `chech_signature_and_encryption`
2. Verify user is in chat
3. Verify all `media_ids` exist, belong to this user (`owner_id == user.id`), and have `message_id IS NULL`
4. Create message
5. Update `message_id` on all media attachments
6. Create notification event for other participants
7. Commit transaction

---

### List message media / Список медиа сообщения

```
GET /private-message/{message_id}/media/
GET /group-message/{message_id}/media/
```

**Response (200):**
```json
{
  "items": [
    {
      "id": "uuid-media-1",
      "mime_type": "image/jpeg",
      "file_size": 245678,
      "creation_datetime": "2026-06-08T12:00:00Z"
    }
  ]
}
```

---

### Download media / Скачивание медиа

```
GET /private-message/media/{media_id}
GET /group-message/media/{media_id}
```

**Response (200):**
```json
{
  "id": "uuid-media-1",
  "mime_type": "image/jpeg",
  "file_size": 245678,
  "encrypted_file": "<base64 bytes>",
  "signature": "<base64 bytes>",
  "owner_id": "uuid-user",
  "creation_datetime": "2026-06-08T12:00:00Z"
}
```

**Access check / Проверка доступа:** User must be a participant of the chat that the message belongs to.

---

### Delete media / Удаление медиа

```
DELETE /private-message/media/{media_id}/
DELETE /group-message/media/{media_id}/
```

Only allowed for the owner (`owner_id == user.id`). If media is already attached to a message, the message remains — just without the attachment.

---

## Signature verification / Проверка подписи

### Text messages / Текстовые сообщения

Existing function `chech_signature_and_encryption`:
1. Parse `PGPMessage` from `encrypted_message`
2. Parse `PGPSignature` from `signature`
3. Parse `PGPKey` from `user.public_key`
4. Verify: `public_key.verify(subject=message_bytes, signature=signature)`
5. Check: `message.is_encrypted`

### Media files / Медиафайлы

New function `check_media_signature`:
1. Parse `PGPSignature` from `signature`
2. Parse `PGPKey` from `user.public_key`
3. Verify: `public_key.verify(subject=encrypted_file_bytes, signature=signature)`

No `PGPMessage` parsing — just detached signature verification of raw bytes.

---

## Client flow / Поток на клиенте

### Upload / Загрузка

```
1. User selects files + writes text
2. Encrypt locally (parallel):
   - Text → PGP encrypt + sign → encrypted_message + signature
   - Each file → PGP encrypt + sign → encrypted_file + signature
3. Upload media (parallel, with progress):
   POST /private-message/{chat_id}/media/upload
   → { id: "media-uuid" }
   Retry on failure (up to 3 times)
4. Send message (when all media uploaded):
   POST /private-message/{chat_id}
   Body: { encrypted_message, signature, media_ids: [...] }
5. If message send fails → retry (media already on server as orphan)
```

### Download / Получение

```
1. GET /private-message/s/{chat_id} — list messages
   Response includes media: [{id, mime_type, file_size}]
2. UI shows only metadata (no download yet)
3. User clicks attachment:
   GET /private-message/media/{media_id}
   → receives encrypted_file + signature
   → decrypt locally via PGP
   → display file
```

---

## Storage abstraction / Абстракция хранилища

```
┌─────────────────────┐
│   MediaStorage      │
│   (Protocol/ABC)    │
│                     │
│ save(data) → id     │
│ load(id) → data     │
│ delete(id)          │
└─────────┬───────────┘
          │
  ┌───────┼───────┐
  │               │
  ▼               ▼
DatabaseStorage  S3Storage (future)
```

Current implementation: `DatabaseStorage` — stores blobs in `media_blob_data` table.

Future: `S3Storage` — stores blobs in S3, `media_blob_data` row is not created.

Switch via `MEDIA_STORAGE_TYPE` in `.env`.

---

## Configuration / Конфигурация

New settings in `settings.py`:

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `MAX_MEDIA_SIZE_BYTES` | int | 52428800 (50 MB) | Maximum media file size |
| `MEDIA_STORAGE_TYPE` | str | "database" | Storage backend: "database" or "s3" |

---

## Files to modify/create / Файлы для изменения/создания

| # | Action | File |
|---|--------|------|
| 1 | Add `MediaAttachment` model | `server/src/messages/models.py` |
| 2 | Add `MediaBlobData` model | `server/src/messages/models.py` |
| 3 | Add media schemas, update `CreateMessage` | `server/src/messages/schemas.py` |
| 4 | Add `check_media_signature` | `server/src/messages/services.py` |
| 5 | Add `MediaStorage` abstraction + `DatabaseStorage` | `server/src/messages/storage.py` (new) |
| 6 | Add `MAX_MEDIA_SIZE_BYTES`, `MEDIA_STORAGE_TYPE` | `server/src/settings.py` |
| 7 | Add endpoints: upload, list, download, delete, update `create_message` | `server/src/messages/router.py` |
| 8 | Alembic migration (2 tables) | `server/src/migrations/versions/` (new) |
| 9 | Update `.env.example` | `server/.env.example` |

---

## Orphan cleanup / Очистка orphan медиа

Out of scope for this implementation. To be handled by a separate background worker:

```sql
DELETE FROM media_attachments
WHERE message_id IS NULL
  AND creation_datetime < NOW() - INTERVAL '15 min'
```

The `media_blob_data` rows are cascade-deleted via FK.

# Security / Безопасность

## Overview / Обзор

Quant is designed with a **zero-knowledge** security model. The server never has access to plaintext messages or private keys.

Quant разработан с моделью безопасности **zero-knowledge**. Сервер никогда не имеет доступа к открытому тексту сообщений или приватным ключам.

---

## PGP Encryption / PGP-шифрование

### How it works / Как это работает

1. **Key Generation / Генерация ключей** — Each user generates a PGP key pair (public + private) on their client.
2. **Public Key Upload / Загрузка публичного ключа** — Users upload their public key to the server via `/auth/change-public-key`.
3. **Message Encryption / Шифрование сообщений** — Messages are encrypted client-side using the recipient's public key.
4. **Message Signing / Подписывание сообщений** — Each message is signed with the sender's private key.
5. **Server Storage / Хранение на сервере** — Only encrypted blobs and signatures are stored.

### Verification / Проверка

When a message is received, the server verifies:

При получении сообщения сервер проверяет:

- The message is actually encrypted (not plaintext)
- The signature is valid for the sender's public key
- The PGP key format is correct (ASCII-armored)

```
Client A                          Server                          Client B
   │                                │                                │
   │── Encrypt msg with B's key ──▶│                                │
   │── Sign with A's private key ─▶│                                │
   │──────── POST encrypted ──────▶│── Verify signature ──▶ Store   │
   │                                │                                │
   │                                │◀────── GET events ────────────│
   │                                │── Notify B of new message ───▶│
   │                                │                                │
   │                                │◀── GET encrypted messages ───│
   │                                │── Return encrypted blob ─────▶│
   │                                │                                │
   │                                │                        Decrypt │
   │                                │                   with B's private key
```

---

## Zero-Knowledge Model / Модель Zero-Knowledge

### What the server knows / Что знает сервер

- User IDs and email addresses
- Chat participants (who talks to whom)
- Message timestamps and sizes
- Event counts (unread notifications)

### What the server does NOT know / Что сервер НЕ знает

- **Message content** — all messages are PGP-encrypted
- **Private keys** — never uploaded to the server
- **User identities beyond email** — no personal data stored
- **Message semantics** — encrypted data is opaque to the server

---

## Threat Model / Модель угроз

### Protected against / Защита от

| Threat / Угроза | Protection / Защита |
|-----------------|---------------------|
| Server compromise / Взлом сервера | Messages remain encrypted / Сообщения остаются зашифрованными |
| Database leak / Утечка базы данных | Only encrypted blobs exposed / Доступны только зашифрованные данные |
| Man-in-the-middle / Человек посередине | PGP signatures verify authenticity / PGP-подписи подтверждают подлинность |
| Passive eavesdropping / Пассивное прослушивание | End-to-end encryption / Сквозное шифрование |
| Message forgery / Подделка сообщений | Digital signatures prevent tampering / Цифровые подписи предотвращают篡改 |

### Not protected against / Не защищает от

| Threat / Угроза | Reason / Причина |
|-----------------|------------------|
| Compromised client / Взломанный клиент | Attacker has access to private keys / У атакующего есть приватные ключи |
| Lost private key / Потерянный приватный ключ | Messages cannot be recovered / Сообщения не могут быть восстановлены |
| Metadata analysis / Анализ метаданных | Server still knows who talks to whom / Сервер всё ещё знает, кто с кем общается |
| Social engineering / Социальная инженерия | Outside technical scope / Вне технической области |

---

## Authentication / Аутентификация

- **Bearer tokens** — stored in database with 1-hour lifetime
- **Password hashing** — handled by `fastapi-users` (bcrypt/argon2)
- **Email verification** — required in production, optional in debug mode
- **Role-based access** — users can only access chats they participate in

---

## Security Recommendations / Рекомендации по безопасности

1. **Use strong PGP keys** — minimum 4096-bit RSA or Ed25519
2. **Never share private keys** — keep them on the client only
3. **Verify key fingerprints** — out-of-band verification prevents MITM
4. **Keep clients updated** — security patches are critical
5. **Use HTTPS in production** — transport encryption is still needed
6. **Rotate access tokens** — tokens expire after 1 hour

1. **Используйте сильные PGP-ключи** — минимум 4096-битный RSA или Ed25519
2. **Никогда не передавайте приватные ключи** — храните их только на клиенте
3. **Проверяйте фингерпринты ключей** — внеполосная проверка предотвращает MITM
4. **Обновляйте клиенты** — патчи безопасности критически важны
5. **Используйте HTTPS в продакшене** — транспортное шифрование всё ещё нужно
6. **Ротируйте токены доступа** — токены истекают через 1 час

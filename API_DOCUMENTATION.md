# 📱 RRR Messenger API Documentation

**Версия:** 1.0.0  
**Язык:** Python (FastAPI)  
**Базовый URL:** `http://localhost:8000`  
**Формат данных:** JSON

---

## 📋 Оглавление

1. [Введение](#введение)
2. [Требования к аутентификации](#требования-к-аутентификации)
3. [Аутентификация и авторизация](#аутентификация-и-авторизация)
4. [Структура ответов API](#структура-ответов-api)
5. [Endpoints](#endpoints)
   - [Аутентификация](#аутентификация)
   - [Пользователи](#пользователи)
   - [Чаты](#чаты)
   - [Сообщения](#сообщения)
   - [Файлы](#файлы)
   - [WebSocket](#websocket)
6. [Коды ошибок](#коды-ошибок)
7. [Примеры использования](#примеры-использования)

---

## Введение

Timess Messenger API — это REST API для мессенджера с поддержкой:
- 👤 Управления пользователями
- 💬 Создания и управления чатами
- 📨 Отправки и получения сообщений
- 🔊 Голосовых сообщений
- 📎 Обмена файлами
- 🔗 WebSocket для real-time общения
- ⭐ Закрепления сообщений
- 👍 Реакций на сообщения
- 🚫 Блокировки пользователей

---

## Требования к аутентификации

Все endpoints (кроме `/auth/register` и `/auth/login`) требуют передачи **токена доступа** в заголовке `Authorization`.

**Формат:**
```
Authorization: Bearer <access_token>
```

---

## Аутентификация и авторизация

### Типы токенов
- **Bearer Token** — JWT токен для аутентификации в каждом запросе

### Получение токена
Токен получается при регистрации или входе и используется в заголовке `Authorization` всех защищённых endpoints.

---

## Структура ответов API

### Успешный ответ (200, 201, 204)

**Для одного ресурса:**
```json
{
  "id": 1,
  "name": "Example",
  "created_at": "2026-08-20T12:00:00Z"
}
```

**Для списка ресурсов:**
```json
[
  {"id": 1, "name": "Item 1"},
  {"id": 2, "name": "Item 2"}
]
```

### Ошибочный ответ

```json
{
  "detail": "Error description"
}
```

**Заголовок:** `Content-Type: application/json`  
**Кодировка:** UTF-8

---

## Endpoints

### 🔐 Аутентификация

#### 1. POST /auth/register
Регистрация нового пользователя

**Параметры:**
| Параметр | Тип    | Обязательный | Ограничения    | Описание |
|----------|--------|--------------|----------------|---------|
| login    | string |      ✅      | 3-100 символов | Логин пользователя (уникальный) |
| username | string |      ✅      | 1-100 символов | Имя пользователя |
| password | string |      ✅      | 4-128 символов | Пароль |

**Запрос:**
```bash
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "login": "john_doe",
    "username": "John Doe",
    "password": "secure_password123"
  }'
```

**Успешный ответ (201):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user_id": 1,
  "username": "John Doe"
}
```

**Ошибки:**
- `400` — Логин уже занят или неверные параметры

---

#### 2. POST /auth/login
Вход в систему

**Параметры:**
| Параметр | Тип    | Обязательный | Ограничения    | Описание |
|----------|--------|--------------|----------------|---------|
| login    | string |      ✅      | 1-100 символов | Логин пользователя |
| password | string |      ✅      | 4-128 символов | Пароль |

**Запрос:**
```bash
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "login": "john_doe",
    "password": "secure_password123"
  }'
```

**Успешный ответ (200):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user_id": 1,
  "username": "John Doe"
}
```

**Ошибки:**
- `401` — Неверный логин или пароль

---

#### 3. GET /auth/me
Получить информацию текущего пользователя

**Авторизация:** ✅ Требуется

**Запрос:**
```bash
curl -X GET http://localhost:8000/auth/me \
  -H "Authorization: Bearer <access_token>"
```

**Успешный ответ (200):**
```json
{
  "id": 1,
  "accountid": "acc_123",
  "username": "John Doe",
  "usernameid": "john_doe",
  "bio": "Software Developer",
  "birthday": "1990-01-15",
  "avatar": "/storage/avatars/abc123.jpg"
}
```

---

### 👤 Пользователи

#### 1. GET /users/
Поиск пользователей

**Параметры запроса:**
| Параметр | Тип    | Обязательный | Описание |
|----------|--------|--------------|---------|
| query    | string |      ✅      | Поисковый запрос (имя, логин) |

**Авторизация:** ✅ Требуется

**Запрос:**
```bash
curl -X GET "http://localhost:8000/users/?query=john" \
  -H "Authorization: Bearer <access_token>"
```

**Успешный ответ (200):**
```json
[
  {
    "id": 1,
    "username": "John Doe",
    "usernameid": "john_doe",
    "avatar": "/storage/avatars/abc123.jpg"
  }
]
```

---

#### 2. GET /users/{user_id}
Получить профиль пользователя

**Параметры пути:**
| Параметр | Тип     | Описание |
|----------|---------|---------|
| user_id  | integer | ID пользователя |

**Авторизация:** ✅ Требуется

**Запрос:**
```bash
curl -X GET http://localhost:8000/users/1 \
  -H "Authorization: Bearer <access_token>"
```

**Успешный ответ (200):**
```json
{
  "id": 1,
  "username": "John Doe",
  "usernameid": "john_doe",
  "bio": "Software Developer",
  "birthday": "1990-01-15",
  "avatar": "/storage/avatars/abc123.jpg",
  "status": "online",
  "last_seen": "2026-08-20T12:00:00Z"
}
```

**Ошибки:**
- `404` — Пользователь не найден

---

#### 3. PUT /users/me
Обновить профиль текущего пользователя

**Параметры:**
| Параметр  | Тип    | Обязательный | Описание|
|-----------|--------|--------------|---------|
| username  | string |      ❌      | Новое имя пользователя |
| usernameid| string |      ❌      | Новый ID пользователя (уникальный) |
| bio 	    | string |      ❌      | Биография |
| birthday  | string |      ❌      | Дата рождения (YYYY-MM-DD) |

**Авторизация:** ✅ Требуется

**Запрос:**
```bash
curl -X PUT http://localhost:8000/users/me \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "John Smith",
    "bio": "Developer & Designer"
  }'
```

**Успешный ответ (200):**
```json
{
  "id": 1,
  "username": "John Smith",
  "usernameid": "john_smith",
  "bio": "Developer & Designer",
  "birthday": "1990-01-15",
  "avatar": "/storage/avatars/abc123.jpg"
}
```

**Ошибки:**
- `400` — usernameid уже занят

---

#### 4. POST /users/me/avatar
Загрузить аватар

**Параметры (multipart/form-data):**
| Параметр | Тип  | Обязательный | Описание |
|----------|------|--------------|---------|
| avatar   | file |      ✅      | Файл изображения (JPEG, PNG, GIF и т.д.) |

**Авторизация:** ✅ Требуется

**Запрос:**
```bash
curl -X POST http://localhost:8000/users/me/avatar \
  -H "Authorization: Bearer <access_token>" \
  -F "avatar=@/path/to/avatar.jpg"
```

**Успешный ответ (200):**
```json
{
  "avatar": "/storage/avatars/abc123xyz.jpg"
}
```

**Ошибки:**
- `400` — Файл не является изображением

---

#### 5. POST /users/me/status
Обновить статус пользователя

**Параметры:**
| Параметр | Тип    | Обязательный | Описание |
|----------|--------|--------------|----------|
| status   | string |      ✅      | Статус (например: "online", "offline", "away") |
| last_seen| string |      ✅      | ISO 8601 timestamp последнего активного времени |

**Авторизация:** ✅ Требуется

**Запрос:**
```bash
curl -X POST http://localhost:8000/users/me/status \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "status": "online",
    "last_seen": "2026-08-20T12:00:00Z"
  }'
```

**Успешный ответ (200):**
```json
{
  "status": "updated"
}
```

---

#### 6. GET /users/{user_id}/status
Получить статус пользователя

**Параметры пути:**
| Параметр |   Тип   | Описание |
|----------|---------|----------|
| user_id  | integer | ID пользователя |

**Авторизация:** ✅ Требуется

**Запрос:**
```bash
curl -X GET http://localhost:8000/users/1/status \
  -H "Authorization: Bearer <access_token>"
```

**Успешный ответ (200):**
```json
{
  "status": "online",
  "last_seen": "2026-08-20T12:00:00Z"
}
```

---

#### 7. POST /users/{user_id}/block
Заблокировать пользователя

**Параметры пути:**
| Параметр |   Тип   | Описание |
|----------|---------|----------|
| user_id  | integer | ID пользователя для блокировки |

**Авторизация:** ✅ Требуется

**Запрос:**
```bash
curl -X POST http://localhost:8000/users/2/block \
  -H "Authorization: Bearer <access_token>"
```

**Успешный ответ (200):**
```json
{
  "success": true
}
```

---

#### 8. DELETE /users/{user_id}/block
Разблокировать пользователя

**Параметры пути:**
| Параметр |   Тип   | Описание |
|----------|---------|----------|
| user_id  | integer | ID пользователя для разблокировки |

**Авторизация:** ✅ Требуется

**Запрос:**
```bash
curl -X DELETE http://localhost:8000/users/2/block \
  -H "Authorization: Bearer <access_token>"
```

**Успешный ответ (200):**
```json
{
  "success": true
}
```

---

#### 9. GET /users/{user_id}/block-status
Получить статус блокировки

**Параметры пути:**
| Параметр |   Тип   | Описание |
|----------|---------|----------|
| user_id  | integer | ID пользователя |

**Авторизация:** ✅ Требуется

**Запрос:**
```bash
curl -X GET http://localhost:8000/users/2/block-status \
  -H "Authorization: Bearer <access_token>"
```

**Успешный ответ (200):**
```json
{
  "i_blocked": false,
  "blocked_me": false,
  "blocked": false
}
```

---

#### 10. DELETE /users/me
Удалить аккаунт

**Авторизация:** ✅ Требуется

**Запрос:**
```bash
curl -X DELETE http://localhost:8000/users/me \
  -H "Authorization: Bearer <access_token>"
```

**Успешный ответ (200):**
```json
{
  "success": true,
  "message": "Account deleted"
}
```

**Ошибки:**
- `400` — Аккаунт уже удалён

---

### 💬 Чаты

#### 1. GET /chats/
Получить список всех чатов текущего пользователя

**Авторизация:** ✅ Требуется

**Запрос:**
```bash
curl -X GET http://localhost:8000/chats/ \
  -H "Authorization: Bearer <access_token>"
```

**Успешный ответ (200):**
```json
[
  {
    "id": 1,
    "name": "John Smith",
    "is_private": true,
    "is_favorite": false,
    "members": [1, 2],
    "last_message": {
      "id": 100,
      "content": "Hello!",
      "created_at": "2026-08-20T11:30:00Z",
      "sender_id": 2,
      "is_read": false,
      "voice_duration": null,
      "file": null
    },
    "avatar": "/storage/avatars/user2.jpg",
    "deleted": false
  }
]
```

---

#### 2. POST /chats/private
Создать или получить личный чат

**Параметры:**
| Параметр |   Тип   | Обязательный | Описание |
|----------|---------|--------------|----------|
| user_id  | integer |      ✅      | ID пользователя для создания личного чата |

**Авторизация:** ✅ Требуется

**Запрос:**
```bash
curl -X POST http://localhost:8000/chats/private \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": 2
  }'
```

**Успешный ответ (200):**
```json
{
  "id": 1,
  "name": "John Smith",
  "avatar": "/storage/avatars/user2.jpg",
  "is_private": true,
  "members": [1, 2]
}
```

---

#### 3. POST /chats/favorite
Создать или получить чат "Избранное"

**Авторизация:** ✅ Требуется

**Запрос:**
```bash
curl -X POST http://localhost:8000/chats/favorite \
  -H "Authorization: Bearer <access_token>"
```

**Успешный ответ (200):**
```json
{
  "id": 5,
  "name": "Избранное",
  "avatar": "/storage/bookmark.png",
  "is_private": true,
  "is_favorite": true,
  "members": [1],
  "last_message": null
}
```

---

#### 4. DELETE /chats/{chat_id}/delete-for-me
Удалить чат только для себя

**Параметры пути:**
| Параметр |   Тип   | Описание |
|----------|---------|----------|
| chat_id  | integer | ID чата  |

**Авторизация:** ✅ Требуется

**Запрос:**
```bash
curl -X DELETE http://localhost:8000/chats/1/delete-for-me \
  -H "Authorization: Bearer <access_token>"
```

**Успешный ответ (200):**
```json
{
  "success": true
}
```

---

#### 5. DELETE /chats/{chat_id}/delete-for-all
Удалить чат для всех участников (только личные чаты)

**Параметры пути:**
| Параметр |   Тип   | Описание |
|----------|---------|----------|
| chat_id  | integer | ID чата  |

**Авторизация:** ✅ Требуется

**Запрос:**
```bash
curl -X DELETE http://localhost:8000/chats/1/delete-for-all \
  -H "Authorization: Bearer <access_token>"
```

**Успешный ответ (200):**
```json
{
  "success": true
}
```

**Ошибки:**
- `400` — Удаление для всех доступно только для личных чатов

---

#### 6. POST /chats/{chat_id}/pins
Закрепить сообщение

**Параметры пути:**
| Параметр |   Тип   | Описание |
|----------|---------|----------|
| chat_id  | integer | ID чата  |

**Параметры:**
|  Параметр  |   Тип   | Обязательный | Описание |
|------------|---------|--------------|----------|
| message_id | integer |      ✅      | ID сообщения для закрепления |

**Авторизация:** ✅ Требуется

**Запрос:**
```bash
curl -X POST http://localhost:8000/chats/1/pins \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "message_id": 100
  }'
```

**Успешный ответ (200):**
```json
{
  "success": true
}
```

---

#### 7. DELETE /chats/{chat_id}/pins/{message_id}
Открепить сообщение

**Параметры пути:**
|  Параметр  |   Тип   | Описание |
|------------|---------|----------|
| chat_id    | integer | ID чата  |
| message_id | integer | ID сообщения |

**Авторизация:** ✅ Требуется

**Запрос:**
```bash
curl -X DELETE http://localhost:8000/chats/1/pins/100 \
  -H "Authorization: Bearer <access_token>"
```

**Успешный ответ (200):**
```json
{
  "success": true
}
```

---

#### 8. GET /chats/{chat_id}/pins
Получить закреплённые сообщения

**Параметры пути:**
| Параметр |   Тип   | Описание |
|----------|---------|----------|
| chat_id  | integer | ID чата  |

**Авторизация:** ✅ Требуется

**Запрос:**
```bash
curl -X GET http://localhost:8000/chats/1/pins \
  -H "Authorization: Bearer <access_token>"
```

**Успешный ответ (200):**
```json
[
  {
    "message_id": 100,
    "content": "Important message",
    "sender_id": 1,
    "created_at": "2026-08-20T10:00:00Z",
    "voice_duration": null,
    "file": null
  }
]
```

---

### 📨 Сообщения

#### 1. GET /messages/
Получить сообщения из чата

**Параметры запроса:**
| Параметр |   Тип   | Обязательный | Описание |
|----------|---------|--------------|----------|
| chat_id  | integer |      ✅      | ID чата  |
| limit    | integer |      ❌      | Количество сообщений (по умолчанию 50) |
| before_id| integer |      ❌      | Загрузить сообщения до этого ID (для пагинации) |

**Авторизация:** ✅ Требуется

**Запрос:**
```bash
curl -X GET "http://localhost:8000/messages/?chat_id=1&limit=20" \
  -H "Authorization: Bearer <access_token>"
```

**Успешный ответ (200):**
```json
[
  {
    "id": 100,
    "chat_id": 1,
    "sender_id": 2,
    "content": "Hello!",
    "created_at": "2026-08-20T11:30:00Z",
    "is_read": true,
    "voice_duration": null,
    "file": null,
    "reactions": [
      {
        "emoji": "👍",
        "count": 1,
        "user_reacted": true
      }
    ]
  }
]
```

---

#### 2. POST /messages/
Отправить сообщение

**Параметры:**
| Параметр |   Тип   | Обязательный | Описание |
|----------|---------|--------------|----------|
| chat_id  | integer |      ✅      | ID чата  |
| content  | string  |      ✅      | Текст сообщения |

**Авторизация:** ✅ Требуется

**Запрос:**
```bash
curl -X POST http://localhost:8000/messages/ \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "chat_id": 1,
    "content": "Hello, how are you?"
  }'
```

**Успешный ответ (200):**
```json
{
  "id": 101,
  "chat_id": 1,
  "sender_id": 1,
  "content": "Hello, how are you?",
  "created_at": "2026-08-20T11:35:00Z",
  "is_read": false,
  "voice_duration": null,
  "file": null,
  "reactions": []
}
```

**Ошибки:**
- `403` — Пользователь заблокирован или удалил аккаунт

---

#### 3. PUT /messages/{message_id}/read
Отметить сообщение как прочитанное

**Параметры пути:**
|  Параметр  |   Тип   | Описание |
|------------|---------|----------|
| message_id | integer | ID сообщения |

**Авторизация:** ✅ Требуется

**Запрос:**
```bash
curl -X PUT http://localhost:8000/messages/100/read \
  -H "Authorization: Bearer <access_token>"
```

**Успешный ответ (200):**
```json
{
  "id": 100,
  "is_read": true
}
```

---

#### 4. PUT /messages/chat/{chat_id}/read-all
Отметить все сообщения в чате как прочитанные

**Параметры пути:**
| Параметр |   Тип   | Описание |
|----------|---------|----------|
| chat_id  | integer | ID чата  |

**Авторизация:** ✅ Требуется

**Запрос:**
```bash
curl -X PUT http://localhost:8000/messages/chat/1/read-all \
  -H "Authorization: Bearer <access_token>"
```

**Успешный ответ (200):**
```json
{
  "success": true
}
```

---

#### 5. GET /messages/unread/counts
Получить количество непрочитанных сообщений в каждом чате

**Авторизация:** ✅ Требуется

**Запрос:**
```bash
curl -X GET http://localhost:8000/messages/unread/counts \
  -H "Authorization: Bearer <access_token>"
```

**Успешный ответ (200):**
```json
{
  "1": 3,
  "2": 0,
  "5": 2
}
```

---

#### 6. POST /messages/{message_id}/reaction
Добавить или убрать реакцию на сообщение

**Параметры пути:**
|  Параметр  |   Тип   | Описание |
|------------|---------|----------|
| message_id | integer | ID сообщения |

**Параметры:**
| Параметр |   Тип  | Обязательный | Описание |
|----------|--------|--------------|----------|
| emoji    | string |      ✅      | Эмодзи (например: 👍, ❤️, 😂) |

**Авторизация:** ✅ Требуется

**Запрос:**
```bash
curl -X POST http://localhost:8000/messages/100/reaction \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "emoji": "👍"
  }'
```

**Успешный ответ (200):**
```json
{
  "success": true,
  "action": "added"
}
```

---

#### 7. POST /messages/voice
Загрузить голосовое сообщение

**Параметры (multipart/form-data):**
| Параметр |   Тип   | Обязательный | Описание |
|----------|---------|--------------|----------|
| chat_id  | integer |      ✅      | ID чата  |
| voice    | file    |      ✅      | Аудиофайл (MP3, WAV и т.д.) |
| duration | integer |      ✅      | Длительность в миллисекундах |
| waveform | string  |      ✅      | JSON строка с данными волны (для визуализации) |

**Авторизация:** ✅ Требуется

**Запрос:**
```bash
curl -X POST http://localhost:8000/messages/voice \
  -H "Authorization: Bearer <access_token>" \
  -F "chat_id=1" \
  -F "voice=@/path/to/voice.mp3" \
  -F "duration=5000" \
  -F "waveform=[0.1,0.2,0.3,0.2,0.1]"
```

**Успешный ответ (200):**
```json
{
  "id": 102,
  "chat_id": 1,
  "sender_id": 1,
  "content": "",
  "created_at": "2026-08-20T11:40:00Z",
  "is_read": false,
  "voice_duration": 5000,
  "file": {
    "id": 50,
    "original_name": "voice.mp3",
    "mime_type": "audio/mpeg",
    "path": "/storage/voices/abc123.mp3"
  }
}
```

---

#### 8. POST /messages/{message_id}/voice-played
Отметить голосовое сообщение как прослушанное

**Параметры пути:**
|  Параметр  |   Тип   | Описание |
|------------|---------|----------|
| message_id | integer | ID голосового сообщения |

**Авторизация:** ✅ Требуется

**Запрос:**
```bash
curl -X POST http://localhost:8000/messages/102/voice-played \
  -H "Authorization: Bearer <access_token>"
```

**Успешный ответ (200):**
```json
{
  "message_id": 102,
  "voice_played": true
}
```

---

### 📎 Файлы

#### 1. POST /files/upload
Загрузить файл

**Параметры (multipart/form-data):**
| Параметр | Тип | Обязательный | Описание |
|----------|-----|--------------|----------|
| file     |file |      ✅      | Файл для загрузки |

**Авторизация:** ✅ Требуется

**Запрос:**
```bash
curl -X POST http://localhost:8000/files/upload \
  -H "Authorization: Bearer <access_token>" \
  -F "file=@/path/to/document.pdf"
```

**Успешный ответ (200):**
```json
{
  "id": 50,
  "original_name": "document.pdf",
  "mime_type": "application/pdf",
  "path": "/storage/files/abc123xyz.pdf",
  "uploaded_by": 1
}
```

---

#### 2. GET /files/download/{file_id}
Скачать файл

**Параметры пути:**
| Параметр |   Тип   | Описание |
|----------|---------|----------|
| file_id  | integer | ID файла |

**Авторизация:** ✅ Требуется

**Запрос:**
```bash
curl -X GET http://localhost:8000/files/download/50 \
  -H "Authorization: Bearer <access_token>" \
  -o document.pdf
```

**Успешный ответ (200):**
Скачивание файла с заголовками:
```
Content-Type: application/pdf
Content-Disposition: attachment; filename="document.pdf"
```

**Ошибки:**
- `404` — Файл не найден

---

### 🔗 WebSocket

#### 1. WebSocket /ws/chat/{chat_id}

Подключение к чату для real-time обмена сообщениями

**Параметры пути:**
| Параметр |   Тип   | Описание |
|----------|---------|----------|
| chat_id  | integer | ID чата для подключения |

**Авторизация:** ✅ Требуется (через query параметр или заголовок)

**Примеры использования:**

**JavaScript/WebSocket API:**
```javascript
// Подключение
const token = localStorage.getItem('access_token');
const ws = new WebSocket(
  `ws://localhost:8000/ws/chat/1?token=${token}`
);

// Отправка сообщения
ws.onopen = () => {
  ws.send('Hello, this is a real-time message!');
};

// Получение сообщения
ws.onmessage = (event) => {
  const message = JSON.parse(event.data);
  console.log('Received:', message);
};

// Ошибка подключения
ws.onerror = (error) => {
  console.error('WebSocket error:', error);
};

// Разъединение
ws.onclose = () => {
  console.log('Disconnected from chat');
};
```

**Python (asyncio):**
```python
import asyncio
import websockets
import json

async def connect_to_chat():
    token = "your_access_token"
    uri = f"ws://localhost:8000/ws/chat/1?token={token}"
    
    async with websockets.connect(uri) as websocket:
        # Отправка сообщения
        await websocket.send("Hello from Python!")
        
        # Получение сообщений
        async for message in websocket:
            print(f"Received: {message}")

asyncio.run(connect_to_chat())
```

**Формат сообщений:**

Входящее сообщение (текст):
```
"Hello, how are you?"
```

Исходящее сообщение (JSON):
```json
{
  "id": 101,
  "chat_id": 1,
  "sender_id": 1,
  "content": "Hello, how are you?",
  "created_at": "2026-08-20T11:35:00Z"
}
```

Системные события:
```json
{
  "type": "message_pinned"
}
```

```json
{
  "type": "reaction_updated",
  "message_id": 100,
  "reactions": [
    {"emoji": "👍", "count": 2, "user_reacted": true}
  ]
}
```

```json
{
  "type": "chat_deleted",
  "chat_id": 1,
  "delete_for": "all",
  "user_id": 2
}
```

**Ошибки:**
- Отключение при неверной авторизации
- Отключение при удалении чата

---

## Коды ошибок

| Код     |      Описание         |                             Решение                                     |
|---------|-----------------------|-------------------------------------------------------------------------|
| **400** |      Bad Request      |          Проверьте корректность параметров запроса 			    |
| **401** |      Unauthorized     |          Добавьте токен в заголовок `Authorization`                     |
| **403** |      Forbidden        | У вас нет доступа к этому ресурсу (например, пользователь заблокирован) |
| **404** |      Not Found        |          Ресурс не найден (пользователь, чат, сообщение)                |
| **500** | Internal Server Error |            Ошибка на сервере, попробуйте позже                          |
| **503** |  Service Unavailable  |           Сервис временно недоступен                                    |

---

## Примеры использования

### Пример 1: Полный цикл регистрации и отправки сообщения

```javascript
// 1. Регистрация
const registerResponse = await fetch('http://localhost:8000/auth/register', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    login: 'john_doe',
    username: 'John Doe',
    password: 'secure_password123'
  })
});

const { access_token } = await registerResponse.json();
localStorage.setItem('access_token', access_token);

// 2. Поиск пользователя
const searchResponse = await fetch('http://localhost:8000/users/?query=jane', {
  headers: { 'Authorization': `Bearer ${access_token}` }
});
const users = await searchResponse.json();
const targetUserId = users[0].id;

// 3. Создание личного чата
const chatResponse = await fetch('http://localhost:8000/chats/private', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${access_token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({ user_id: targetUserId })
});
const { id: chatId } = await chatResponse.json();

// 4. Отправка сообщения
const messageResponse = await fetch('http://localhost:8000/messages/', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${access_token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    chat_id: chatId,
    content: 'Hi Jane, how are you?'
  })
});

const message = await messageResponse.json();
console.log('Message sent:', message);
```

### Пример 2: Загрузка аватара

```javascript
const token = localStorage.getItem('access_token');
const fileInput = document.getElementById('avatar-input');
const formData = new FormData();
formData.append('avatar', fileInput.files[0]);

const response = await fetch('http://localhost:8000/users/me/avatar', {
  method: 'POST',
  headers: { 'Authorization': `Bearer ${token}` },
  body: formData
});

const { avatar } = await response.json();
document.getElementById('user-avatar').src = avatar;
```

### Пример 3: Real-time чат с WebSocket

```javascript
class ChatManager {
  constructor(chatId, token) {
    this.chatId = chatId;
    this.token = token;
    this.ws = null;
  }

  connect() {
    this.ws = new WebSocket(
      `ws://localhost:8000/ws/chat/${this.chatId}?token=${this.token}`
    );

    this.ws.onmessage = (event) => {
      const message = JSON.parse(event.data);
      this.onMessageReceived(message);
    };

    this.ws.onerror = (error) => {
      console.error('WebSocket error:', error);
    };
  }

  sendMessage(content) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(content);
    }
  }

  onMessageReceived(message) {
    console.log('New message:', message);
    // Обновить UI
  }

  disconnect() {
    if (this.ws) {
      this.ws.close();
    }
  }
}

// Использование
const chat = new ChatManager(1, 'your_access_token');
chat.connect();
chat.sendMessage('Hello!');
```

---

## Стек технологий

- **Backend Framework:** FastAPI (Python)
- **Database:** SQLAlchemy ORM
- **Authentication:** JWT (Bearer Token)
- **Real-time:** WebSocket
- **File Storage:** Локальная файловая система (`/storage`)

---

## Среды выполнения

### Разработка (Development)
```
Base URL: http://localhost:8000
```

### CORS Configuration
```
Allowed Origins:
- http://localhost:5500
- http://127.0.0.1:5500
- https://dae9-72-56-42-19.ngrok-free.app
- http://localhost:8000
```

---

## Поддержка и контакты

Если у вас возникли вопросы или найдены ошибки в API:
- 📧 Создайте Issue в репозитории
- 💻 Свяжитесь с разработчиком
- 📚 Проверьте примеры кода выше

---

**Версия документации:** 1.0.0  
**Последнее обновление:** 2026-08-20  
**Статус:** Active ✅

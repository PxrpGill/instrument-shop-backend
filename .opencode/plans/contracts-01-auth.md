# Plan: Contracts — Auth Module

## Task Overview
Привести существующий `apps/users` (роуты `/v1/customers/...`) к контракту `/api/auth/...` и добавить недостающие эндпоинты: `logout`, `forgot-password`, `reset-password`. Сейчас регистрация/логин/refresh/me реализованы, но shape ответа и поля отличаются от контракта.

Источник истины: `contracts/auth/*.json`, `contracts/README.md` (раздел «Авторизация»).

## Scope (контракты)
| Контракт | Эндпоинт | Auth |
| --- | --- | --- |
| `auth/register.json` | `POST /api/auth/register` | — |
| `auth/login.json` | `POST /api/auth/login` | — |
| `auth/refresh.json` | `POST /api/auth/refresh` | — |
| `auth/logout.json` | `POST /api/auth/logout` | ✔ |
| `auth/me.json` | `GET /api/auth/me` | ✔ |
| `auth/forgot-password.json` | `POST /api/auth/forgot-password` | — |
| `auth/reset-password.json` | `POST /api/auth/reset-password` | — |

## Gap-анализ (текущее → требуемое)
- **Путь**: `/api/v1/customers/...` → `/api/auth/...`. Старые пути можно удалить (фронта на них нет) или оставить как алиас на 1 релиз.
- **Customer.id**: решено — оставляем UUID, в JSON отдаём как строку (`"id": "550e8400-e29b-41d4-a716-446655440000"`). Sequential int не используем по соображениям безопасности (утечка количества клиентов, IDOR-enumeration, предсказуемость JWT-claim). Пример в контрактах `auth/*.json` и `shared/` нужно поправить с `42` на UUID-строку — это часть deliverable плана. Фронт должен трактовать `id` как opaque string.
- **Customer.username**: сейчас нет — контракт требует `username` (2..64). Добавить поле `username` (nullable, заполняется на регистрации), мигрировать существующих как `first_name`.
- **Response shape**:
  - register/login возвращают `{access_token, refresh_token, token_type, expires_in, user: {...}}` — сейчас иначе. Привести.
  - `expires_in` = TTL access в секундах = `SIMPLE_JWT.ACCESS_TOKEN_LIFETIME.total_seconds()`.
- **logout**: blacklist refresh-токена (`rest_framework_simplejwt.token_blacklist`). Подключить app, мигрировать.
- **forgot-password**: всегда 200 (не выдаём существование email). Генерация одноразового токена → отправка email. Решить отправку: dev — console backend, prod — SMTP. Токен в `PasswordResetToken` модели (token, customer, expires_at, used_at).
- **reset-password**: принять токен + новый пароль, инвалидировать токен, выдать новые пары (по контракту) или вернуть 200.

## Deliverables
1. Миграция: добавить `Customer.username`, создать `PasswordResetToken`. `Customer.id` остаётся UUIDField — не трогаем.
0. Правка контрактов: в `contracts/auth/register.json`, `login.json`, `me.json`, `refresh.json` заменить пример `"id": 42` на UUID-строку. Это сделать **до** реализации, чтобы пример в контракте совпал с реальным ответом.
2. Подключить `rest_framework_simplejwt.token_blacklist` в `INSTALLED_APPS` + миграции.
3. Перенести роутер в `apps/users/api/auth_controllers.py`, новый префикс — `/api/auth/`.
4. Привести схемы `RegisterResponseSchema`, `LoginResponseSchema`, `UserSchema`, `RefreshResponseSchema` к контракту.
5. Реализовать `logout`, `forgot-password`, `reset-password` сервисами в `apps/users/services/`.
6. Rate limit: `login` 5/min (есть), `register` 10/min (есть), `refresh` 20/min (есть), добавить `forgot-password` ~3/min (антиспам).
7. Email-отправка: `apps/shared/services/email.py` (использует Django `send_mail`) — `MAIL_FROM`, `RESET_PASSWORD_URL_TEMPLATE` в env.

## Implementation Order
1. Refactor: переименовать роутер, изменить пути, обновить ответы — без новых полей.
2. Добавить `username` миграцией.
3. Подключить blacklist + endpoint `logout`.
4. `PasswordResetToken` + `forgot-password` + `reset-password`.
5. Email backend (console для dev).
6. Тесты на каждый эндпоинт + happy-path/edge-cases (повторный токен, истёкший, чужой).

## Files to Modify / Create
- `apps/users/models.py` — `+username`, `+PasswordResetToken`
- `apps/users/migrations/0007_*`
- `apps/users/api/auth_controllers.py` (новый, перенесённый из `controllers.py`)
- `apps/users/services/customer_service.py` (правки `generate_tokens` → отдать `expires_in`)
- `apps/users/services/password_reset_service.py` (новый)
- `apps/users/schemas.py` — переименовать/добавить схемы по контракту
- `apps/shared/services/email.py` (новый)
- `instrument_shop/api.py`, `settings.py` — `token_blacklist` app + email settings

## Completion Criteria
- Все 7 эндпоинтов отвечают JSON, идентичным `contracts/auth/*.json` `responses.200.example` (поля, имена, типы).
- Ошибки в формате `shared/error.json` с кодами из README.
- `logout` действительно blacklist'ит refresh — последующий `refresh` возвращает 401 `INVALID_TOKEN`.
- forgot-password всегда 200, токен живёт ≤ N часов, повторный reset-password с тем же токеном — 400 `INVALID_TOKEN`.
- Тесты ≥ 1 на endpoint на каждый response code из контракта.

## Dependencies
- Не зависит от `contracts-00-shared-foundation` напрямую, но желателен общий error-handler оттуда — иначе придётся писать локально и потом мигрировать.
- Не блокирует ничего, кроме `contracts-07-favorites` (нужен `Authorization: Bearer`).

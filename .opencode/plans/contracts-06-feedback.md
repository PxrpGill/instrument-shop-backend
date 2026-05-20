# Plan: Contracts — Feedback Module

## Task Overview
Эндпоинт приёма обратной связи с формы на сайте. Простейший модуль, но требует антиспам.

Источник истины: `contracts/feedback/submit.json`.

## Scope
| Контракт | Эндпоинт | Auth |
| --- | --- | --- |
| `feedback/submit.json` | `POST /api/feedback` | — |

## Модель
- `FeedbackMessage`:
  - `name`, `email` (EmailField), `phone` (опц.), `message` (TextField)
  - `created_at`
  - `ip_address` (для антиспама / аналитики)
  - `processed_at` (nullable, отметка «обработано»)

## Deliverables
1. Модель + миграция (новый app `apps/feedback`).
2. Pydantic-схема `FeedbackSubmitRequest` с EmailStr и валидацией.
3. Endpoint `POST /api/feedback` — сохранить в БД + опц. отправить email админу.
4. **Throttling**: django-ratelimit по IP — 5/мин (или из контракта, уточнить).
5. На 429 — формат `shared/error.json` с `RATE_LIMITED`.
6. Админка: фильтры по дате/processed.
7. Тесты:
   - 201 happy
   - 422 валидация (email, message length)
   - 429 после превышения лимита (использовать `override_settings` для лимита)

## Implementation Order
1. Модель + миграция + админка.
2. Endpoint + схемы.
3. Throttling + 429.
4. Email-уведомление (опц.).

## Files to Modify / Create
- `apps/feedback/` (новый app)
- `instrument_shop/settings.py`, `instrument_shop/api.py`

## Completion Criteria
- Ответ 1-в-1 с контрактом (200/201, точно проверить в `feedback/submit.json`).
- Превышение rate limit → 429 + `shared/error.json`.
- Сообщение видно в админке.

## Dependencies
- Зависит от: `contracts-00-shared-foundation` (Error format).
- Параллелится со всеми остальными модулями.

# Plan: Contracts — Favorites Module

## Task Overview
Реализовать «избранное» — список товаров, сохранённый авторизованным пользователем. Сейчас функционала нет.

Источник истины: `contracts/favorites/list.json`, `contracts/favorites/toggle.json`.

## Scope (контракты)
| Контракт | Эндпоинт | Auth |
| --- | --- | --- |
| `favorites/list.json` | `GET /api/favorites` | ✔ |
| `favorites/toggle.json` | `POST /api/favorites/{product_id}` | ✔ |
| `favorites/toggle.json` | `DELETE /api/favorites/{product_id}` | ✔ |

## Модель
- `Favorite` (Customer FK + Product FK + created_at, `unique_together = (customer, product)`).
- Идемпотентность:
  - POST уже существующего → 200 (не 409).
  - DELETE несуществующего → 204.
  - 404 — только если `product_id` отсутствует в БД (не если просто не в избранном).

## Deliverables
1. Модель `Favorite` + миграция (новый app `apps/favorites` или внутри `apps/users`).
2. Admin (для отладки).
3. Pydantic-схемы:
   - `FavoritesListResponse` — массив `shared/product` (listing-формат) + `total`.
   - `FavoriteToggleResponse {is_favorite: bool, total: int}` для POST.
4. Сервис `favorites_service.py` (add/remove идемпотентно, list с prefetch товаров).
5. Permissions: пользователь видит только своё, любой авторизованный customer имеет доступ к своему списку (новое permission `view_own_favorites`, `edit_own_favorites` — или просто `IsAuthenticated`).
6. Эндпоинты в `apps/favorites/controllers.py`, роут `/api/favorites`.
7. Тесты:
   - 401 без токена
   - POST 200 happy + повторный POST 200
   - DELETE 204 happy + повторный DELETE 204
   - POST 404 на несуществующий product
   - GET list пустой/непустой
   - Snapshot: товар архивирован → исключать из ответа? Уточнить (вероятно, исключать).

## Implementation Order
1. Модель + миграция.
2. POST + DELETE (идемпотентность).
3. GET list.
4. Тесты + edge cases.

## Files to Modify / Create
- `apps/favorites/` (новый app)
- `instrument_shop/settings.py`, `instrument_shop/api.py`

## Completion Criteria
- Ответ POST `{is_favorite: true, total: N}` совпадает с контрактом.
- DELETE — 204 без тела.
- list возвращает товары в формате `shared/product` (listing).
- Идемпотентность подтверждена тестами.

## Dependencies
- Зависит от: `contracts-00-shared-foundation` (Picture, Error), `contracts-01-auth` (Authorization Bearer), `contracts-02-catalog` (shape `shared/product` listing).
- Самый поздний по очерёдности.

# Plan: Contracts — News Module

## Task Overview
Создать новый Django app `apps/news` для управления новостями магазина. Сейчас в проекте новостей нет.

Источник истины: `contracts/news/list.json`, `contracts/news/single.json`, `contracts/shared/news-card.json`.

## Scope (контракты)
| Контракт | Эндпоинт |
| --- | --- |
| `news/list.json` | `GET /api/news?tab=&page=&per_page=` (фильтрация по табу + пагинация) |
| `news/single.json` | `GET /api/news/{slug}` |

## Модель
- `NewsTab` (slug, title, order) — табы фильтра, задаются админом. Slug `all` — служебный, обозначает «без фильтра» (на бекенде это можно реализовать или как настоящую запись, или как зарезервированное значение).
- `NewsArticle`:
  - `slug` (unique, slugify из title)
  - `title`, `description` (short, для карточки)
  - `content` (HTML, для single страницы) — TODO: проверить `news/single.json`
  - `date` (DateTimeField, default `now`, отображается как ISO 8601 UTC)
  - `tab` FK → `NewsTab` (один таб на статью). Или M2M, если нужно несколько — уточнить.
  - `picture` FK → `apps.shared.Image` (для карточки и/или single)
  - `status` (draft/published) — только published попадает в API.

`title` и `description` страницы списка (`"Новости магазина"`, описание сверху) — это статика страницы. Решения:
- Хранить в `NewsPage` singleton (см. `contracts-03-pages`, путь B), либо
- Хранить в `apps/news/models.py::NewsPageSettings` (singleton).

## Deliverables
1. Миграции под `NewsTab`, `NewsArticle`, `NewsPageSettings`.
2. Админка: Unfold-стиль, prepopulated slug, фильтр по tab/status.
3. Pydantic-схемы:
   - `NewsCardSchema` (`shared/news-card`).
   - `NewsListResponse {title, description, tabs, current_slug_tab, items, meta}`.
   - `NewsSingleResponse` — по контракту.
4. Сервис `news_query.py` для фильтрации/пагинации.
5. Эндпоинты в `apps/news/controllers.py` под роутом `/api/news`.
6. Регистрация в `instrument_shop/api.py`.
7. Тесты: list (tab=all, tab=existing, tab=unknown → 200 с пустыми items или 404 — уточнить), single (404 на несуществующий slug, 200 happy).

## Implementation Order
1. Модели + миграция.
2. Админка.
3. `GET /api/news/{slug}` (single).
4. `GET /api/news` (list + tab filter + pagination).
5. NewsPageSettings (статика страницы).
6. Тесты.

## Files to Modify / Create
- `apps/news/` (новый app)
- `instrument_shop/settings.py` — `INSTALLED_APPS += ["apps.news"]`
- `instrument_shop/api.py` — `add_router("/api/news", ...)`

## Completion Criteria
- Ответы 1-в-1 с контрактом.
- `tab=all` возвращает все новости; неизвестный tab — поведение согласовано (404 или пусто).
- `per_page` ограничен 50 (как в notes контракта).
- HTML контента санитайзится.

## Dependencies
- Зависит от: `contracts-00-shared-foundation` (Picture, Pagination, Error, sanitize).
- Параллелится с: `contracts-02-catalog`, `contracts-03-pages`, `contracts-06-feedback`, `contracts-07-favorites`.

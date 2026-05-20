# Plan: Contracts — Shared Foundation

## Task Overview
Реализовать переиспользуемую инфраструктуру, на которую опираются все остальные плановые модули из `contracts/`. Этот план — фундамент: его нужно завершить до `contracts-03-catalog`, `contracts-04-pages`, `contracts-05-news`, `contracts-07-favorites`, потому что они напрямую используют Picture/Pagination/Error/SiteLink из shared.

Источник истины: `contracts/shared/*.json` и `contracts/README.md` (раздел «Что бекенд должен предусмотреть, помимо роутов»).

## Scope (контракты)
- `shared/picture.json` — Image модель с автонарезкой webp/avif + mobile-вариант
- `shared/pagination.json` — единый формат `meta: {page, per_page, total_pages, total_items}`
- `shared/error.json` — единый формат ошибок `{error: {code, message, fields?}}` для всех 4xx/5xx
- `shared/site-link.json` — переиспользуемый `{title, href}` для CTA-кнопок
- `shared/product.json`, `shared/product-category.json`, `shared/news-card.json` — Pydantic-схемы для переиспользования (без реализации эндпоинтов — они появятся в `contracts-03/05`)

## Deliverables

### 1. Image / Picture pipeline
- Модель `apps/shared/models.py::Image` (или `apps/media`) с полями `source_desktop`, `source_mobile`, `webp_desktop`, `avif_desktop`, `webp_mobile`, `avif_mobile`, `alt_text`.
- Добавить `pillow-avif-plugin` в `requirements.txt` + `docker/shared/requirements.txt`.
- Сигнал `post_save` → задача конверсии. Решить: celery, django-q или встроенный `transaction.on_commit` + sync (для MVP). Рекомендация для MVP: sync через `transaction.on_commit`, не блокируя ответ админки.
- Pydantic-схема `PictureSchema` с `original/webp/avif`, каждое — `{src, mobile?}`. Опциональные подэлементы, чтобы фронт корректно рендерил во время прогрева.
- Хелпер сериализации модели Image → PictureSchema.

### 2. Error handling
- Кастомный exception `BusinessError(code: str, message: str, status: int, fields: dict | None = None)`.
- Глобальный exception handler в `instrument_shop/api.py` (`api.exception_handler`) для:
  - `BusinessError` → `{error: {code, message, fields?}}`
  - `pydantic.ValidationError` → `422 VALIDATION_ERROR` с маппингом ошибок в `error.fields`
  - `Http404` → `404 NOT_FOUND`
  - всё остальное → `500 INTERNAL_ERROR`
- Готовые коды из README: `INVALID_TOKEN`, `UNAUTHORIZED`, `INVALID_CREDENTIALS`, `NOT_FOUND`, `EMAIL_ALREADY_TAKEN`, `VALIDATION_ERROR`, `RATE_LIMITED`, `INTERNAL_ERROR` — в `apps/shared/errors.py`.

### 3. Pagination
- Утилита `paginate(queryset, page, per_page, max_per_page=50) -> (items, meta)`.
- Pydantic-схема `PaginationMeta {page, per_page, total_pages, total_items}`.

### 4. SiteLink
- Pydantic-схема `SiteLink {title: str, href: str}` для CTA-блоков (используется в `pages/home`, `feedback`, `legal`-навигации и т.п.).

### 5. HTML sanitization
- Добавить `bleach` в зависимости.
- Утилита `sanitize_html(text: str) -> str` с whitelist тегов (`h2`, `h3`, `p`, `ul`, `ol`, `li`, `blockquote`, `br`, `strong`, `em`, `a`).
- Применяется в админке (или на save модели) для полей `content`, `description`, `parameters`, поскольку фронт использует `dangerouslySetInnerHTML`.

### 6. CORS / Throttling sanity-check
- В `settings.py` CORS и кеш уже настроены (Task 15). Сверить с README: `http://localhost:3000` обязан быть в `CORS_ALLOWED_ORIGINS`.
- Throttling middleware/decorator уже есть через `django-ratelimit`. Документировать использование для `contracts-06-feedback` и `contracts-02-auth` (forgot-password).

## Implementation Order
1. Image модель + миграция, без конверсии (только desktop original).
2. `PictureSchema` + сериализатор.
3. Конвертер webp/avif (`pillow-avif-plugin`), сигнал post_save.
4. Mobile-вариант (повтор шагов 1-3 для `source_mobile`).
5. `BusinessError` + exception handler.
6. Pagination + SiteLink схемы.
7. Sanitize-утилита.

## Files to Modify / Create
- `requirements.txt`, `docker/shared/requirements.txt`
- `apps/shared/` (новый app): `models.py`, `schemas.py`, `errors.py`, `services/image_pipeline.py`, `services/sanitize.py`, `utils/pagination.py`
- `instrument_shop/api.py` — регистрация exception handler
- `instrument_shop/settings.py` — `INSTALLED_APPS += ["apps.shared"]`

## Completion Criteria
- В админке можно загрузить изображение → в БД появляются derivative-файлы.
- `PictureSchema` сериализует все доступные форматы; отсутствующие — пропускает (не `null`).
- Любая ошибка API возвращается в формате `shared/error.json`.
- Pagination meta совпадает с `shared/pagination.json` 1-в-1.
- Тесты: pipeline (загрузка → webp/avif), exception handler, paginator (edge: page > total_pages → пустой items, total_items > 0).

## Dependencies
- Блокирует: `contracts-03-catalog`, `contracts-04-pages`, `contracts-05-news`, `contracts-07-favorites`.
- Параллелится с: `contracts-02-auth` (auth Picture не использует, но error handler понадобится — этот пункт можно вытащить отдельно, если хочется параллельности).

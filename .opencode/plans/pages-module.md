# Plan: Pages Module — Content Blocks with Page Builder

## Task Overview
Создать новый раздел в админке для управления информационными страницами сайта.
Пользователь создаёт страницы и наполняет их контентными блоками разных типов.
Блоки имеют независимый статус (черновик/опубликован) и могут переиспользоваться на разных страницах.
Данные отдаются через Django Ninja API.

## Current State
- В проекте 4 приложения: users, products, orders, core
- Админка на Unfold
- API на Django Ninja с роутами в `instrument_shop/api.py`
- Есть абстрактная модель `TimeStampedModel` в `apps/products/models.py`
- Используется `JSONField` для гибких данных (см. `Product.parameters`)

## Architecture

### Модели

**Page** (extends TimeStampedModel):
- title — заголовок страницы
- slug — уникальный URL-идентификатор
- meta_title — SEO заголовок (опционально)
- meta_description — SEO описание (опционально)
- og_image — изображение для OG (опционально)
- blocks — M2M к ContentBlock через PageBlock

**ContentBlock** (extends TimeStampedModel):
- title — внутреннее название для админки
- block_type — тип блока (TextChoices: hero, text, faq, features, gallery, reviews, banner, video, statistics, contacts)
- content — JSONField с данными блока
- status — черновик/опубликован

**PageBlock** (through model, extends TimeStampedModel):
- page — FK к Page
- block — FK к ContentBlock
- order — порядковый номер для сортировки

Типы блоков и структура их JSON:
1. **hero** — `{title, subtitle, text, button_text, button_url, background_image, background_color}`
2. **text** — `{content, alignment}`
3. **faq** — `{items: [{question, answer}]}`
4. **features** — `{items: [{icon, title, description}]}`
5. **gallery** — `{images: [{image, alt_text}]}`
6. **reviews** — `{items: [{author_name, author_title, text, avatar, rating}]}`
7. **banner** — `{image, link_url, link_text, alt_text}`
8. **video** — `{embed_url, title, description}`
9. **statistics** — `{items: [{number, label, prefix, suffix}]}`
10. **contacts** — `{address, phone, email, working_hours, map_coordinates}`

### Admin (Unfold)
- PageAdmin: list display (title, slug), prepopulated slug, inline PageBlock (сортировка)
- ContentBlockAdmin: list display (title, block_type, status), фильтры, list_editable status
- PageBlockInline: выбор блока + поле order, autocomplete для блоков

### API Endpoints (публичные, без авторизации)
- `GET /api/v1/public/pages/{slug}/` — страница с опубликованными блоками в правильном порядке

## Implementation Order

### 1. Setup — создать app `pages`
- Создать `apps/pages/` с __init__.py, apps.py
- Добавить `apps.pages` в INSTALLED_APPS
- Выполнить `makemigrations`

### 2. Models — `apps/pages/models.py`
- Page, ContentBlock, PageBlock модели
- BlockTypeChoices, BlockStatusChoices
- Все verbose_name/help_text на русском
- __str__ для всех моделей

### 3. Admin — `apps/pages/admin.py`
- PageAdmin с PageBlockInline
- ContentBlockAdmin
- Использовать Unfold ModelAdmin

### 4. Schemas — `apps/pages/schemas.py`
- PageOut, ContentBlockOut для API

### 5. Services — `apps/pages/services.py`
- get_page_by_slug, get_published_blocks

### 6. API — `apps/pages/controllers.py`
- GET /pages/{slug} — публичный эндпоинт
- Зарегистрировать роутер в `instrument_shop/api.py`

### 7. Tests — `apps/pages/tests/`
- test_models.py — создание моделей, __str__, ordering, constraints
- test_api.py — API возвращает страницу, только опубликованные блоки, сортировка, 404

### 8. Final Verification
- Миграции
- Тесты
- Линтинг (black, isort)

## Files to Create
| File | Purpose |
|------|---------|
| `apps/pages/__init__.py` | Пакет |
| `apps/pages/apps.py` | AppConfig |
| `apps/pages/models.py` | Модели |
| `apps/pages/admin.py` | Админка Unfold |
| `apps/pages/schemas.py` | Pydantic схемы |
| `apps/pages/services.py` | Бизнес-логика |
| `apps/pages/controllers.py` | API эндпоинты |
| `apps/pages/tests/__init__.py` | Тест-пакет |
| `apps/pages/tests/test_models.py` | Тесты моделей |
| `apps/pages/tests/test_api.py` | Тесты API |
| `apps/pages/migrations/__init__.py` | Миграции |

## Files to Modify
| File | Change |
|------|--------|
| `instrument_shop/settings.py` | Добавить `apps.pages` в INSTALLED_APPS |
| `instrument_shop/api.py` | Добавить pages роутер |

## Dependencies
1. Сначала модели + миграции
2. Потом админка (зависит от моделей)
3. Потом API (зависит от моделей)
4. Потом тесты (зависит от всего)

## Delegation Map
- **database-normalization-architect** — модели и миграции
- **senior-backend-django-ninja** — API, админка, схемы, сервисы
- **senior-python-tester** — тесты

## Completion Criteria
- ✅ Админка с разделом "Страницы" и "Блоки контента"
- ✅ Можно создать страницу, выбрать блоки, отсортировать их
- ✅ У блоков есть статус черновик/опубликован
- ✅ API отдаёт страницу только с опубликованными блоками, в правильном порядке
- ✅ Все 10 типов блоков имеют корректную JSON-структуру
- ✅ Тесты проходят
- ✅ Black/isort проходят

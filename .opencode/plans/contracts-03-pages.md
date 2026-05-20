# Plan: Contracts — Pages (Static Content)

## Task Overview
Полностью переписать `apps/pages`: убрать универсальный page builder (`ContentBlock` + `PageBlock`) и заменить на **жёстко типизированные per-page singleton-модели**, соответствующие контрактам `contracts/pages/*`.

**Решение зафиксировано:** структура страниц фиксирована продуктом, универсальный builder не нужен. Текущий `apps/pages` сносим (модели, миграции, схемы, тесты) и пишем заново. Существующие миграции `apps/pages` можно либо удалить и накатить заново (если данных в БД нет / dev), либо написать миграцию-сноску `RunPython` для очистки и далее обычные миграции.

Источник истины: `contracts/pages/*.json`.

## Scope (контракты)
| Контракт | Эндпоинт | Описание |
| --- | --- | --- |
| `pages/home.json` | `GET /api/pages/home` | Hero / About company / Reviews / Showcase / News CTA — каждый блок опционален |
| `pages/about-us.json` | `GET /api/pages/about-us` | TODO: прочитать контракт |
| `pages/buyers.json` | `GET /api/pages/buyers` | Условия покупки / оплаты (оплата только в магазине) |
| `pages/feedback.json` | `GET /api/pages/feedback` | Тексты страницы обратной связи (форма отправляет в `contracts-04-feedback`) |
| `pages/legal/{slug}.json` | `GET /api/pages/legal/{slug}` | Один эндпоинт на 3 документа: `privacy-policy`, `user-agreement`, `personal-data-consent`. TOC формируется из `sections[].id` + `sections[].title`. |

## Gap-анализ
- Текущий `apps/pages` (универсальный page builder, миграции `0001_*` и далее) — выбрасываем полностью. В dev-БД таблицы дропаем, в prod данных пока нет.
- В контракте `home` HTML присутствует в `hero.description`, `about_company.content` — требует `sanitize_html` из `contracts-00-shared-foundation`.
- `poster` — это `shared/Picture` (FK на `apps.shared.Image`).
- `showcase.showcases[].products` ссылается на товары — нужны связи с `Product` (M2M через through-model для порядка).
- Отзывы (`reviews.reviews[]`) — отдельная сущность с `title`, `description`, `grade` (1..5), `author.fullName`, `author.icon` (FK Picture). M2M `HomePage ↔ Review` через through-model для порядка.
- `legal/{slug}` — модель `LegalDocument` (slug — choices: `privacy-policy`, `user-agreement`, `personal-data-consent`) + through-model `LegalSection` (id-anchor, title, content text с `\n\n`).

## Deliverables
1. Снести текущий `apps/pages` (`models.py`, `admin.py`, `controllers.py`, `schemas.py`, `services.py`, `tests/`, миграции). Оставить только `apps.py`, `__init__.py`.
2. Новые модели:
   - **HomePage** (singleton) с опциональными секциями:
     - hero: `hero_title`, `hero_description` (HTML), `hero_button_title`, `hero_button_href`, `hero_poster` (FK Picture, nullable)
     - about_company: `about_title`, `about_content` (HTML), `about_poster` (FK Picture, nullable)
     - reviews: `reviews_title` + through-model `HomePageReview` (с `order`) → `Review` из отдельного app `apps/reviews` (см. ниже)
     - showcase: `showcase_title`, `showcase_button_title`, `showcase_button_href` + through-model `HomePageShowcase` (title группы) → M2M на Product через `HomePageShowcaseProduct` (order)
     - news_cta: `news_cta_title`, `news_cta_description`, `news_cta_button_title`, `news_cta_button_href`, `news_cta_poster` FK Picture
   - **AboutUsPage**, **BuyersPage**, **FeedbackPage** — singleton с полями ровно под соответствующие JSON-контракты (нужно прочитать `about-us.json`, `buyers.json`, `feedback.json` при реализации, чтобы зафиксировать поля).
   - **LegalDocument** (slug PK с choices, `title`, `last_updated: CharField` в формате `ДД.ММ.ГГГГ`) + **LegalSection** (FK doc, `anchor_id`, `title`, `content` TextField, `order`).
3. Singleton-паттерн: переопределить `save()` с `pk = 1`, в админке скрыть кнопки add/delete. Альтернатива — пакет `django-solo`, но проще руками.
4. Pydantic-схемы 1-в-1 под `contracts/pages/*.json`: имена полей точно как в контракте (`hero`, `about_company`, `news_cta` с подчёркиваниями).
5. Сериализатор: если опциональная секция (например, `hero_title` пустой) — секция целиком не возвращается в JSON (а не `null`).
6. Endpoint'ы:
   - `GET /api/pages/home` → HomePage
   - `GET /api/pages/about-us` → AboutUsPage
   - `GET /api/pages/buyers` → BuyersPage
   - `GET /api/pages/feedback` → FeedbackPage
   - `GET /api/pages/legal/{slug}` → LegalDocument by slug, 404 на неизвестный
7. Админка (django-unfold):
   - Singleton-страницы: inline для review/showcase/legal-sections, drag-and-drop порядок (как сейчас в page builder admin).
   - LegalDocument: 3 фикс. записи, новый не создаётся (после первичного сидирования).
8. Sanitize HTML в `save()` на HTML-полях (hero_description, about_content, и т.п.).

## Implementation Order
1. Снос старого `apps/pages` + миграция-сноска (RunPython drop_table + DeleteModel).
2. Новый app `apps/reviews` (см. отдельный раздел «Reviews app» ниже) — модель + админка. Делается до HomePage, потому что HomePage держит M2M на Review.
3. `LegalDocument` + `LegalSection` — самое простое (plain text, без Picture, без Product).
4. `AboutUsPage`, `BuyersPage`, `FeedbackPage` (плоские singleton — после прочтения соотв. JSON).
5. `HomePage` — самая сложная (Picture, Product, Review).
6. Sanitize HTML hook.
7. Admin для всех (singleton-паттерн + inline).
8. Эндпоинты + Pydantic схемы.
9. Тесты: пустая страница → ключи опциональных секций отсутствуют; полностью заполненная → 1-в-1 с example; 404 на legal slug; ordering в showcase/reviews/sections соблюдён.

## Files to Modify / Create
- `apps/pages/models.py` — переписать или дополнить.
- `apps/pages/admin.py` — singleton-страницы.
- `apps/pages/controllers.py` — роуты `/api/pages/...`.
- `apps/pages/schemas.py` — Pydantic-схемы под контракт.
- Миграция.

## Completion Criteria
- Ответы 1-в-1 с `contracts/pages/*.json`.
- Опциональные поля (например, отсутствующий `hero` на home) **не возвращаются** в JSON (а не `null`) — README §«Правила работы для AI-агента» п.1.
- HTML в админке санитайзится перед сохранением.
- Тесты ≥ 1 happy + 1 «страница не заполнена» + 1 404 (legal) на эндпоинт.

## Reviews app (входит в этот план)

`Review` вынесен в отдельный app `apps/reviews` как глобальная сущность — не принадлежит ни одной странице, админ ведёт общий пул, страницы выбирают нужные через свои through-модели.

**Модель `apps/reviews/models.py::Review`:**
- `title: CharField(255)` — заголовок отзыва
- `description: TextField` — текст
- `grade: PositiveSmallIntegerField` с `validators=[MinValueValidator(1), MaxValueValidator(5)]`
- `author_full_name: CharField(255)`
- `author_icon: ForeignKey("shared.Image", null=True, blank=True)` — аватарка (опциональна по контракту)
- `is_published: BooleanField(default=True)` — для модерации, по умолчанию опубликован
- `created_at`, `updated_at` (TimeStampedModel)
- `Meta.ordering = ["-created_at"]`, `verbose_name = "Отзыв"`, `verbose_name_plural = "Отзывы"`

**Без полей** `target_product` / `target_type` сейчас. Когда понадобятся отзывы на товары — добавим nullable FK `product` отдельной миграцией. YAGNI.

**Админка** (unfold): list_display = `title`, `author_full_name`, `grade`, `is_published`, `created_at`. Фильтры по `grade`, `is_published`. search по `title`, `author_full_name`.

**Публичные эндпоинты** — нет (не в контрактах). Review отдаётся только через `/api/pages/home` → секция `reviews.reviews[]` (только `is_published=True`, в порядке HomePageReview.order).

**Через-модель `HomePageReview`** живёт в `apps/pages`:
- `home_page: FK HomePage`
- `review: FK apps.reviews.Review`
- `order: PositiveIntegerField(default=0)`
- `unique_together = [("home_page", "review")]`, `ordering = ["order"]`

**Регистрация:** `INSTALLED_APPS += ["apps.reviews"]`.

## Dependencies
- Зависит от: `contracts-00-shared-foundation` (Picture, SiteLink, sanitize_html).
- Конфликт с текущим `apps/pages` разрешён: сносим полностью.
- Внутри плана: `apps/reviews` реализуется до HomePage (HomePage держит FK на Review).

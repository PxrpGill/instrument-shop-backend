# API Response Examples — Design Spec

**Date:** 2026-05-20  
**Scope:** добавить примеры ответов во все response-схемы, отображаемые в `/api/docs`

---

## Цель

Swagger UI на `/api/docs` генерируется Django Ninja автоматически, но без примеров поля показываются пустыми или с автоматическими типовыми значениями. Нужно добавить реалистичные примеры для каждой response-схемы, чтобы разработчики фронтенда и интеграторы видели конкретные данные.

---

## Подход

**Метод:** `model_config = ConfigDict(json_schema_extra={"example": {...}})` на каждом response-классе.

- Swagger UI отображает пример в разделе "Example Value" для каждого ответа
- Примеры живут рядом со схемой, не засоряют контроллеры
- Для схем с уже существующим `ConfigDict(from_attributes=True)` — объединяем в одном `ConfigDict`
- Не трогаем request-схемы (RegisterRequest, LoginRequest и т.д.) — только response

---

## Файлы и схемы

### 1. `apps/users/api/auth_schemas.py`
- `UserSchema` — пример пользователя с UUID id, username, email, created_at
- `TokenPair` — пример access/refresh JWT-токенов
- `AuthResponse` — TokenPair + user
- `MessageResponse` — пример сообщения об успехе

### 2. `apps/products/schemas.py`
- `CategorySchema` — пример категории (Дрели, slug "dreli")
- `ProductImageSchema` — пример изображения товара
- `ProductSchema` — пример товара (Перфоратор Bosch GBH 2-28, price, categories, images)

### 3. `apps/products/catalog_schemas.py`
- `ProductListItem` — карточка листинга с poster
- `ProductDetail` — полная карточка с gallery, techicalSpecifications
- `CatalogResponse` — полный ответ `/catalog`
- `CategoryResponse` — ответ `/catalog/categories/{slug}`
- `ProductDetailResponse` — ответ `/catalog/products/{id}`

### 4. `apps/orders/schemas.py`
- `OrderItemResponseSchema` — позиция заказа
- `OrderResponseSchema` — полный заказ с items
- `OrderListResponseSchema` — краткая карточка заказа в списке

### 5. `apps/news/schemas.py`
- `NewsListResponse` — список новостей с tabs, items, meta
- `NewsSingleResponse` — отдельная новость с banner и content

### 6. `apps/favorites/schemas.py`
- `FavoritesListResponse` — список избранных товаров
- `FavoriteToggleResponse` — ответ на добавление/удаление из избранного

### 7. `apps/pages/schemas.py`
- `HomePageOut` — главная страница (hero, about_company, showcase, reviews)
- `BannerPageOut` — страница с баннером (о компании / покупателям)
- `FeedbackPageOut` — страница обратной связи
- `LegalDocumentOut` — юридический документ с sections

### 8. `apps/feedback/schemas.py`
- `FeedbackSubmitResponse` — подтверждение отправки обращения

---

## Правила для примеров

- Товары: реалистичные названия строительных инструментов (перфораторы, дрели, болгарки, шуруповёрты)
- Цены: в рублях, целое число (4990, 12500, 8900)
- Даты: ISO-формат, 2024–2025 год
- JWT-токены: сокращённые, но реалистичные (eyJhbGciOiJIUzI1NiIs...)
- slug: кириллица не используется, латиница строчными (perforator-bosch, dreli)
- Изображения: `/media/products/...` пути

---

## Ограничения

- Не добавляем примеры к request-схемам (уже есть Field descriptions)
- Не добавляем примеры к вспомогательным sub-схемам (PictureSchema, SiteLink, PaginationMeta) — только к корневым response-схемам
- Не меняем логику схем, только `model_config`

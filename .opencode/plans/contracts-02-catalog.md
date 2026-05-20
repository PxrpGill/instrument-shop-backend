# Plan: Contracts — Catalog (Public) Module

## Task Overview
Реализовать публичный каталог по контракту `/api/catalog/*`. У нас уже есть `apps/products` (`Category`, `Product`, `ProductImage`) и публичный API на `/v1/public/products/*`, но shape ответа и фильтры отличаются от контракта. Нужен новый публичный поверхностный слой + расширение модели Product недостающими полями.

Источник истины: `contracts/catalog/*.json`, `contracts/shared/product.json`, `contracts/shared/product-category.json`.

## Scope (контракты)
| Контракт | Эндпоинт |
| --- | --- |
| `catalog/catalog.json` | `GET /api/catalog` (категории + фильтры + товары) |
| `catalog/category.json` | `GET /api/catalog/categories/{slug}` |
| `catalog/product.json` | `GET /api/catalog/products/{id}` |

## Gap-анализ
- **Поле `Product.status`**: сейчас `draft|published|archived`. Контракт хочет публичный `status: {slugStatus: "inStock"|"outOfStock", title: "..."}`. Это маппинг из существующего `Product.availability` (`in_stock`/`out_of_stock`/`on_request`) → `slugStatus` (`inStock`/`outOfStock`). Нужен сериализатор-маппер, `on_request` тоже мапится в `outOfStock` или `inStock` (нужно решить).
- **`descriptionParameters`** (HTML-блоки) и **`techicalSpecifications`** (label/value пары) — этих полей нет на Product. Варианты:
  - Добавить два JSONField (`description_parameters`, `technical_specifications`) — простой путь.
  - Или вынести в отдельные модели `ProductDescriptionBlock`, `ProductSpecificationGroup` с inline-админкой.
  - **Рекомендация**: JSONField для MVP, согласовать схему со фронтом, при росте каталога — нормализовать.
- **`poster`** (главное фото) vs **`gallery`** (все фото). Сейчас `ProductImage` с `is_primary`. Маппинг прямой: `is_primary=True` → poster, остальные → gallery.
- **`category`** в карточке — массив `{title, slug}` (минимум 1). Категория сейчас есть, но в публичной выдаче надо отдавать массив (M2M уже есть).
- **`GET /api/catalog`** — комбинированный ответ: блок категорий, блок фильтров (price range — min/max по всему каталогу, чекбоксы категорий), пагинированный список товаров с фильтром `?categories=&price_min=&price_max=&sort=&page=&per_page=`.
- **`sort`**: `popular | price_asc | price_desc | new`. `popular` — нет метрики, поставить fallback на `-created_at` или ввести `Product.sales_count` (out of MVP — параметризовать).
- **`GET /api/catalog/categories/{slug}`** — страница категории: те же блоки + filter_block ограничен текущей категорией.
- **`GET /api/catalog/products/{id}`** — детальная карточка + `breadcrumbs` (если есть в контракте, проверить).
- **`shared/picture.json`**: каждое фото — объект `Picture` с original/webp/avif. Требует `contracts-00-shared-foundation` (Image pipeline).

## Deliverables
1. Миграция: `Product.description_parameters: JSONField(default=list)`, `Product.technical_specifications: JSONField(default=list)`, опц. `Product.is_popular`/`sales_count`.
2. Изменить `ProductImage.image` на FK к `apps.shared.Image` (либо использовать `Image` напрямую как related). Решение зависит от того, как вписать существующий `ProductImage` в новую Image-инфраструктуру.
3. Новый файл `apps/products/public_api_v2.py` (рабочее имя) с роутером `/api/catalog/*`. Старый `/v1/public/*` оставить временно или удалить.
4. Pydantic-схемы:
   - `PublicCategorySchema {title, slug}` — `shared/product-category`.
   - `PublicProductListSchema` — без gallery/descriptionParameters/techicalSpecifications.
   - `PublicProductDetailSchema` — все поля.
   - `CatalogResponse {categories_block, filter_block, products_block}`.
   - `CategoryResponse` — то же что Catalog, но `filter_block` ограничен категорией.
5. Сервис `apps/products/services/catalog_query.py` — построение QuerySet по фильтрам, пагинация, сортировка.
6. Кеш: GET `/api/catalog` без фильтров — 1 мин; категории — 5 мин (как уже сделано в Task 15, аналогично).
7. Инвалидация кеша по post_save Product/Category/ProductImage.

## Implementation Order
1. Расширение модели Product (новые поля) + миграция.
2. Сериализатор Product → `shared/product` (listing + detail) на новых схемах.
3. `GET /api/catalog/products/{id}` — простейший case.
4. `GET /api/catalog/categories/{slug}` — фильтрация по категории.
5. `GET /api/catalog` — фильтры/сортировка/пагинация.
6. Кеш + инвалидация.
7. Маппинг `availability → status.slugStatus`.
8. Тесты на каждый эндпоинт + edge (несуществующий slug → 404, фильтр price без товаров → пустой items, sort=new).

## Files to Modify / Create
- `apps/products/models.py` — новые поля
- `apps/products/migrations/0008_*`
- `apps/products/public_api.py` — заменить или новый файл `catalog_controllers.py`
- `apps/products/schemas.py` — новые публичные схемы
- `apps/products/services/catalog_query.py` (новый)
- `apps/products/admin.py` — JSON-поля через `unfold` widget
- `instrument_shop/api.py` — `add_router("/api/catalog", ...)`

## Completion Criteria
- Каждый из трёх эндпоинтов отвечает JSON, идентичным example из контракта (включая `slugStatus`, `descriptionParameters`, `techicalSpecifications` с опечаткой).
- Фильтр `?categories=a&categories=b` (повторяющийся ключ) парсится корректно.
- `?sort=popular|price_asc|price_desc|new` работает.
- `meta` совпадает с `shared/pagination`.
- Кеш инвалидируется при post_save Product/Category/ProductImage (как в Task 15).
- Тесты ≥ 5 per-endpoint.

## Dependencies
- Зависит от: `contracts-00-shared-foundation` (Picture, Pagination, Error).
- Параллелится с: `contracts-01-auth`, `contracts-05-news`.

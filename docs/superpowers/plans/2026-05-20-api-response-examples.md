# API Response Examples Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Добавить `json_schema_extra` с реалистичными примерами ответов ко всем response-схемам, чтобы Swagger UI на `/api/docs` отображал "Example Value" для каждого эндпоинта.

**Architecture:** Добавляем `model_config = ConfigDict(json_schema_extra={"example": {...}})` к каждому response-классу. Для схем с уже существующим `ConfigDict(from_attributes=True)` — добавляем `json_schema_extra` в тот же ConfigDict. Примеры — реалистичные данные строительного магазина.

**Tech Stack:** Django Ninja 1.6.2, Pydantic 2.12.5, pytest

---

### Task 1: auth_schemas — UserSchema, TokenPair, AuthResponse, MessageResponse

**Files:**
- Modify: `apps/users/api/auth_schemas.py`
- Test: `apps/users/tests/test_schema_examples.py` (создать)

- [ ] **Step 1: Написать тест**

```python
# apps/users/tests/test_schema_examples.py
from apps.users.api.auth_schemas import AuthResponse, MessageResponse, TokenPair, UserSchema


def test_user_schema_has_example():
    schema = UserSchema.model_json_schema()
    assert "example" in schema


def test_token_pair_has_example():
    schema = TokenPair.model_json_schema()
    assert "example" in schema


def test_auth_response_has_example():
    schema = AuthResponse.model_json_schema()
    assert "example" in schema


def test_message_response_has_example():
    schema = MessageResponse.model_json_schema()
    assert "example" in schema
```

- [ ] **Step 2: Убедиться, что тесты падают**

```bash
pytest apps/users/tests/test_schema_examples.py -v
```
Ожидаем: 4 FAILED — `AssertionError: assert "example" in {...}`

- [ ] **Step 3: Добавить примеры в auth_schemas.py**

Заменить блок response-схем (начиная с `class UserSchema`) на:

```python
from pydantic import ConfigDict

class UserSchema(Schema):
    """contract: /api/auth/me и user в register/login."""

    model_config = ConfigDict(json_schema_extra={"example": {
        "id": "550e8400-e29b-41d4-a716-446655440000",
        "username": "ivan_petrov",
        "email": "ivan@example.ru",
        "created_at": "2024-09-15T10:30:00Z",
    }})

    id: str
    username: str
    email: str
    created_at: datetime


class TokenPair(Schema):
    """Базовая часть ответа auth: access + refresh + meta."""

    model_config = ConfigDict(json_schema_extra={"example": {
        "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoiNTUwZTg0MDAiLCJleHAiOjE3MDAwMDAwMDB9.abc123",
        "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoiNTUwZTg0MDAiLCJ0eXBlIjoicmVmcmVzaCJ9.xyz789",
        "token_type": "bearer",
        "expires_in": 3600,
    }})

    access_token: str
    refresh_token: str
    token_type: str
    expires_in: int


class AuthResponse(TokenPair):
    """register/login: TokenPair + user."""

    model_config = ConfigDict(json_schema_extra={"example": {
        "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoiNTUwZTg0MDAiLCJleHAiOjE3MDAwMDAwMDB9.abc123",
        "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoiNTUwZTg0MDAiLCJ0eXBlIjoicmVmcmVzaCJ9.xyz789",
        "token_type": "bearer",
        "expires_in": 3600,
        "user": {
            "id": "550e8400-e29b-41d4-a716-446655440000",
            "username": "ivan_petrov",
            "email": "ivan@example.ru",
            "created_at": "2024-09-15T10:30:00Z",
        },
    }})

    user: UserSchema


class MessageResponse(Schema):
    model_config = ConfigDict(json_schema_extra={"example": {
        "message": "Письмо для сброса пароля отправлено на указанный email.",
    }})

    message: str
```

- [ ] **Step 4: Запустить тесты**

```bash
pytest apps/users/tests/test_schema_examples.py -v
```
Ожидаем: 4 PASSED

- [ ] **Step 5: Коммит**

```bash
git add apps/users/api/auth_schemas.py apps/users/tests/test_schema_examples.py
git commit -m "feat: добавить примеры ответов в auth_schemas"
```

---

### Task 2: products/schemas — CategorySchema, ProductImageSchema, ProductSchema

**Files:**
- Modify: `apps/products/schemas.py`
- Test: `apps/products/tests/test_schema_examples.py` (создать)

- [ ] **Step 1: Написать тест**

```python
# apps/products/tests/test_schema_examples.py
from apps.products.schemas import CategorySchema, ProductImageSchema, ProductSchema


def test_category_schema_has_example():
    assert "example" in CategorySchema.model_json_schema()


def test_product_image_schema_has_example():
    assert "example" in ProductImageSchema.model_json_schema()


def test_product_schema_has_example():
    assert "example" in ProductSchema.model_json_schema()
```

- [ ] **Step 2: Убедиться, что тесты падают**

```bash
pytest apps/products/tests/test_schema_examples.py -v
```
Ожидаем: 3 FAILED

- [ ] **Step 3: Добавить примеры в products/schemas.py**

Добавить `model_config` к каждому классу. Вставить после строки `from ninja import ModelSchema`:

```python
from pydantic import ConfigDict
```

Обновить классы:

```python
class CategorySchema(ModelSchema):
    """Схема Category для admin API."""

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={"example": {
            "id": 3,
            "slug": "dreli",
            "name": "Дрели",
            "poster": None,
            "created_at": "2024-01-10T08:00:00Z",
            "updated_at": "2024-06-01T12:00:00Z",
        }},
    )

    class Meta:
        model = Category
        fields = ["id", "slug", "name", "poster", "created_at", "updated_at"]


class ProductImageSchema(ModelSchema):
    """Схема ProductImage для admin API."""

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={"example": {
            "id": 7,
            "image": "/media/products/bosch-gbh228-main.jpg",
            "is_primary": True,
            "order": 0,
            "created_at": "2024-03-20T09:15:00Z",
            "updated_at": "2024-03-20T09:15:00Z",
        }},
    )

    class Meta:
        model = ProductImage
        fields = ["id", "image", "is_primary", "order", "created_at", "updated_at"]


class ProductSchema(ModelSchema):
    """Схема Product для admin API."""

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={"example": {
            "id": 42,
            "name": "Перфоратор Bosch GBH 2-28",
            "description": "Мощный перфоратор для профессионального использования",
            "parameters": "",
            "description_parameters": [],
            "technical_specifications": [],
            "price": "12500.00",
            "sku": "BOSCH-GBH228",
            "brand": "Bosch",
            "status": "published",
            "availability": True,
            "categories": [{"id": 1, "slug": "perforatory", "name": "Перфораторы", "poster": None,
                            "created_at": "2024-01-10T08:00:00Z", "updated_at": "2024-01-10T08:00:00Z"}],
            "images": [{"id": 7, "image": "/media/products/bosch-gbh228-main.jpg", "is_primary": True,
                        "order": 0, "created_at": "2024-03-20T09:15:00Z", "updated_at": "2024-03-20T09:15:00Z"}],
            "created_at": "2024-03-15T10:00:00Z",
            "updated_at": "2024-06-10T14:30:00Z",
        }},
    )

    categories: Optional[list[CategorySchema]] = []
    images: Optional[list[ProductImageSchema]] = []

    class Meta:
        model = Product
        fields = [
            "id", "name", "description", "parameters", "description_parameters",
            "technical_specifications", "price", "sku", "brand", "status",
            "availability", "categories", "created_at", "updated_at",
        ]
```

- [ ] **Step 4: Запустить тесты**

```bash
pytest apps/products/tests/test_schema_examples.py -v
```
Ожидаем: 3 PASSED

- [ ] **Step 5: Коммит**

```bash
git add apps/products/schemas.py apps/products/tests/test_schema_examples.py
git commit -m "feat: добавить примеры ответов в products/schemas"
```

---

### Task 3: catalog_schemas — ProductListItem, ProductDetail, CatalogResponse, CategoryResponse, ProductDetailResponse

**Files:**
- Modify: `apps/products/catalog_schemas.py`
- Test: `apps/products/tests/test_catalog_schema_examples.py` (создать)

- [ ] **Step 1: Написать тест**

```python
# apps/products/tests/test_catalog_schema_examples.py
from apps.products.catalog_schemas import (
    CatalogResponse, CategoryResponse, ProductDetail,
    ProductDetailResponse, ProductListItem,
)


def test_product_list_item_has_example():
    assert "example" in ProductListItem.model_json_schema()


def test_product_detail_has_example():
    assert "example" in ProductDetail.model_json_schema()


def test_catalog_response_has_example():
    assert "example" in CatalogResponse.model_json_schema()


def test_category_response_has_example():
    assert "example" in CategoryResponse.model_json_schema()


def test_product_detail_response_has_example():
    assert "example" in ProductDetailResponse.model_json_schema()
```

- [ ] **Step 2: Убедиться, что тесты падают**

```bash
pytest apps/products/tests/test_catalog_schema_examples.py -v
```
Ожидаем: 5 FAILED

- [ ] **Step 3: Добавить примеры в catalog_schemas.py**

Добавить `from pydantic import ConfigDict` в импорты, затем добавить `model_config` к классам:

```python
# В начало файла добавить импорт:
from pydantic import ConfigDict


class ProductListItem(Schema):
    """Карточка товара в листинге (без gallery / detail-полей)."""

    model_config = ConfigDict(json_schema_extra={"example": {
        "id": 42,
        "title": "Перфоратор Bosch GBH 2-28",
        "description": "Мощный перфоратор для профессиональных работ, 880 Вт",
        "sku": "BOSCH-GBH228",
        "price": 12500,
        "category": [{"title": "Перфораторы", "slug": "perforatory"}],
        "status": {"slugStatus": "inStock", "title": "В наличии"},
        "poster": {
            "original": {"src": "/media/products/bosch-gbh228.jpg", "mobile": None},
            "webp": {"src": "/media/products/bosch-gbh228.webp", "mobile": None},
            "avif": None,
        },
    }})

    id: int
    title: str
    description: str
    sku: Optional[str] = None
    price: int
    category: List[ProductCategory]
    status: Optional[ProductStatus] = None
    poster: Optional[PictureSchema] = None


class ProductDetail(Schema):
    """Полная карточка товара на странице товара."""

    model_config = ConfigDict(json_schema_extra={"example": {
        "id": 42,
        "title": "Перфоратор Bosch GBH 2-28",
        "description": "Мощный перфоратор для профессиональных работ, 880 Вт",
        "sku": "BOSCH-GBH228",
        "price": 12500,
        "status": {"slugStatus": "inStock", "title": "В наличии"},
        "category": [{"title": "Перфораторы", "slug": "perforatory"}],
        "gallery": [
            {"original": {"src": "/media/products/bosch-gbh228-1.jpg", "mobile": None}, "webp": None, "avif": None},
            {"original": {"src": "/media/products/bosch-gbh228-2.jpg", "mobile": None}, "webp": None, "avif": None},
        ],
        "descriptionParameters": [
            {"title": "Технические характеристики", "parameters": "<p>Мощность: 880 Вт</p>"}
        ],
        "techicalSpecifications": [
            {"title": "Общие", "specifications": [
                {"label": "Мощность", "value": "880 Вт"},
                {"label": "Масса", "value": "2.9 кг"},
            ]}
        ],
    }})

    id: int
    title: str
    description: str
    sku: Optional[str] = None
    price: int
    status: ProductStatus
    category: List[ProductCategory]
    gallery: Optional[List[PictureSchema]] = None
    descriptionParameters: Optional[List[DescriptionParametersGroup]] = None
    techicalSpecifications: Optional[List[TechSpecificationGroup]] = None


class CatalogResponse(Schema):
    """GET /catalog — главная каталога."""

    model_config = ConfigDict(json_schema_extra={"example": {
        "categories_block": {
            "title": "Категории",
            "categories": [
                {"title": "Перфораторы", "slug": "perforatory"},
                {"title": "Дрели", "slug": "dreli"},
                {"title": "Шуруповёрты", "slug": "shurupoverty"},
            ],
        },
        "filter_block": {
            "price_filter": {"start_range": 1000, "end_range": 50000},
            "categories_filter": {
                "categories": [
                    {"title": "Перфораторы", "slug": "perforatory"},
                    {"title": "Дрели", "slug": "dreli"},
                ]
            },
        },
        "products_block": {
            "title": "Все товары",
            "products": [
                {
                    "id": 42, "title": "Перфоратор Bosch GBH 2-28", "description": "880 Вт",
                    "sku": "BOSCH-GBH228", "price": 12500,
                    "category": [{"title": "Перфораторы", "slug": "perforatory"}],
                    "status": {"slugStatus": "inStock", "title": "В наличии"}, "poster": None,
                }
            ],
            "meta": {"page": 1, "per_page": 12, "total_pages": 5, "total_items": 58},
        },
    }})

    categories_block: CategoriesBlock
    filter_block: CatalogFilterBlock
    products_block: ProductsBlock


class CategoryResponse(Schema):
    """GET /catalog/categories/{slug} — страница категории."""

    model_config = ConfigDict(json_schema_extra={"example": {
        "category": {"title": "Перфораторы", "slug": "perforatory"},
        "filter_block": {
            "price_filter": {"start_range": 2000, "end_range": 45000},
        },
        "products_block": {
            "title": "Перфораторы",
            "products": [
                {
                    "id": 42, "title": "Перфоратор Bosch GBH 2-28", "description": "880 Вт",
                    "sku": "BOSCH-GBH228", "price": 12500,
                    "category": [{"title": "Перфораторы", "slug": "perforatory"}],
                    "status": {"slugStatus": "inStock", "title": "В наличии"}, "poster": None,
                }
            ],
            "meta": {"page": 1, "per_page": 12, "total_pages": 2, "total_items": 18},
        },
    }})

    category: ProductCategory
    filter_block: CategoryFilterBlock
    products_block: ProductsBlock


class ProductDetailResponse(Schema):
    """GET /catalog/products/{id} — карточка товара."""

    model_config = ConfigDict(json_schema_extra={"example": {
        "product": {
            "id": 42, "title": "Перфоратор Bosch GBH 2-28",
            "description": "Мощный перфоратор для профессиональных работ, 880 Вт",
            "sku": "BOSCH-GBH228", "price": 12500,
            "status": {"slugStatus": "inStock", "title": "В наличии"},
            "category": [{"title": "Перфораторы", "slug": "perforatory"}],
            "gallery": [{"original": {"src": "/media/products/bosch-gbh228-1.jpg", "mobile": None}, "webp": None, "avif": None}],
            "descriptionParameters": None,
            "techicalSpecifications": [
                {"title": "Общие", "specifications": [{"label": "Мощность", "value": "880 Вт"}]}
            ],
        },
        "showcase": {
            "title": "Похожие товары",
            "button": {"title": "Все перфораторы", "href": "/catalog/perforatory"},
            "showcases": [
                {
                    "title": "Популярные",
                    "products": [
                        {"id": 43, "title": "Перфоратор Makita HR2470", "description": "780 Вт",
                         "sku": "MAK-HR2470", "price": 9900,
                         "category": [{"title": "Перфораторы", "slug": "perforatory"}],
                         "status": {"slugStatus": "inStock", "title": "В наличии"}, "poster": None}
                    ],
                }
            ],
        },
    }})

    product: ProductDetail
    showcase: Optional[ShowcaseBlock] = None
```

- [ ] **Step 4: Запустить тесты**

```bash
pytest apps/products/tests/test_catalog_schema_examples.py -v
```
Ожидаем: 5 PASSED

- [ ] **Step 5: Коммит**

```bash
git add apps/products/catalog_schemas.py apps/products/tests/test_catalog_schema_examples.py
git commit -m "feat: добавить примеры ответов в catalog_schemas"
```

---

### Task 4: orders/schemas — OrderItemResponseSchema, OrderResponseSchema, OrderListResponseSchema

**Files:**
- Modify: `apps/orders/schemas.py`
- Test: `apps/orders/tests/test_schema_examples.py` (создать)

- [ ] **Step 1: Написать тест**

```python
# apps/orders/tests/test_schema_examples.py
from apps.orders.schemas import OrderItemResponseSchema, OrderListResponseSchema, OrderResponseSchema


def test_order_item_response_has_example():
    assert "example" in OrderItemResponseSchema.model_json_schema()


def test_order_response_has_example():
    assert "example" in OrderResponseSchema.model_json_schema()


def test_order_list_response_has_example():
    assert "example" in OrderListResponseSchema.model_json_schema()
```

- [ ] **Step 2: Убедиться, что тесты падают**

```bash
pytest apps/orders/tests/test_schema_examples.py -v
```
Ожидаем: 3 FAILED

- [ ] **Step 3: Добавить примеры в orders/schemas.py**

Обновить классы `OrderItemResponseSchema`, `OrderResponseSchema`, `OrderListResponseSchema` — добавить `json_schema_extra` в существующий `ConfigDict`:

```python
class OrderItemResponseSchema(BaseModel):
    """Schema for order item in response."""

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={"example": {
            "id": 15,
            "product_id": 42,
            "product_name": "Перфоратор Bosch GBH 2-28",
            "quantity": 2,
            "unit_price": "12500.00",
            "subtotal": "25000.00",
        }},
    )

    id: int
    product_id: int
    product_name: str
    quantity: int
    unit_price: DecimalField
    subtotal: DecimalField


class OrderResponseSchema(BaseModel):
    """Schema for order response (customer view)."""

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={"example": {
            "id": 101,
            "status": "processing",
            "contact_email": "ivan@example.ru",
            "contact_phone": "+7 (916) 123-45-67",
            "first_name": "Иван",
            "last_name": "Петров",
            "address": "г. Москва, ул. Строителей, д. 5, кв. 12",
            "notes": "Позвоните перед доставкой",
            "total_amount": "25000.00",
            "items": [
                {
                    "id": 15, "product_id": 42, "product_name": "Перфоратор Bosch GBH 2-28",
                    "quantity": 2, "unit_price": "12500.00", "subtotal": "25000.00",
                }
            ],
            "created_at": "2024-11-20T14:35:00Z",
            "updated_at": "2024-11-20T14:35:00Z",
        }},
    )

    id: int
    status: OrderStatusField
    contact_email: EmailStr
    contact_phone: str
    first_name: str
    last_name: str
    address: str
    notes: str
    total_amount: DecimalField
    items: list[OrderItemResponseSchema]
    created_at: DatetimeField
    updated_at: DatetimeField


class OrderListResponseSchema(BaseModel):
    """Schema for order list response (summary)."""

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={"example": {
            "id": 101,
            "status": "confirmed",
            "contact_email": "ivan@example.ru",
            "total_amount": "25000.00",
            "items_count": 2,
            "created_at": "2024-11-20T14:35:00Z",
        }},
    )

    id: int
    status: OrderStatusField
    contact_email: EmailStr
    total_amount: DecimalField
    items_count: int
    created_at: DatetimeField
```

- [ ] **Step 4: Запустить тесты**

```bash
pytest apps/orders/tests/test_schema_examples.py -v
```
Ожидаем: 3 PASSED

- [ ] **Step 5: Коммит**

```bash
git add apps/orders/schemas.py apps/orders/tests/test_schema_examples.py
git commit -m "feat: добавить примеры ответов в orders/schemas"
```

---

### Task 5: news/schemas — NewsListResponse, NewsSingleResponse

**Files:**
- Modify: `apps/news/schemas.py`
- Test: `apps/news/tests/test_schema_examples.py` (создать)

- [ ] **Step 1: Написать тест**

```python
# apps/news/tests/test_schema_examples.py
from apps.news.schemas import NewsListResponse, NewsSingleResponse


def test_news_list_response_has_example():
    assert "example" in NewsListResponse.model_json_schema()


def test_news_single_response_has_example():
    assert "example" in NewsSingleResponse.model_json_schema()
```

- [ ] **Step 2: Убедиться, что тесты падают**

```bash
pytest apps/news/tests/test_schema_examples.py -v
```
Ожидаем: 2 FAILED

- [ ] **Step 3: Добавить примеры в news/schemas.py**

Добавить `from pydantic import ConfigDict` в импорты.

```python
class NewsListResponse(Schema):
    model_config = ConfigDict(json_schema_extra={"example": {
        "title": "Новости",
        "description": "Актуальные новости и статьи об инструментах",
        "tabs": [
            {"title": "Все", "slug": "all"},
            {"title": "Обзоры", "slug": "reviews"},
            {"title": "Советы", "slug": "tips"},
        ],
        "current_slug_tab": "all",
        "items": [
            {
                "title": "Новые перфораторы Bosch 2025: обзор линейки",
                "slug": "bosch-perforatory-2025",
                "date": "2025-03-10",
                "description": "Разбираем обновлённую линейку профессиональных перфораторов",
                "poster": {
                    "original": {"src": "/media/news/bosch-2025.jpg", "mobile": None},
                    "webp": None, "avif": None,
                },
            }
        ],
        "meta": {"page": 1, "per_page": 9, "total_pages": 4, "total_items": 35},
    }})

    title: str
    description: str
    tabs: List[NewsTabOut]
    current_slug_tab: str
    items: List[NewsCardSchema]
    meta: PaginationMeta


class NewsSingleResponse(Schema):
    model_config = ConfigDict(json_schema_extra={"example": {
        "banner": {
            "title": "Новые перфораторы Bosch 2025: обзор линейки",
            "description": "Разбираем обновлённую линейку профессиональных перфораторов Bosch",
            "poster": {
                "original": {"src": "/media/news/bosch-2025.jpg", "mobile": None},
                "webp": None, "avif": None,
            },
        },
        "content": "<p>В 2025 году Bosch представила обновлённую серию перфораторов...</p>",
        "date": "2025-03-10",
        "slug": "bosch-perforatory-2025",
    }})

    banner: NewsSingleBanner
    content: str
    date: str
    slug: str
```

- [ ] **Step 4: Запустить тесты**

```bash
pytest apps/news/tests/test_schema_examples.py -v
```
Ожидаем: 2 PASSED

- [ ] **Step 5: Коммит**

```bash
git add apps/news/schemas.py apps/news/tests/test_schema_examples.py
git commit -m "feat: добавить примеры ответов в news/schemas"
```

---

### Task 6: favorites/schemas — FavoritesListResponse, FavoriteToggleResponse

**Files:**
- Modify: `apps/favorites/schemas.py`
- Test: `apps/favorites/tests/test_schema_examples.py` (создать)

- [ ] **Step 1: Написать тест**

```python
# apps/favorites/tests/test_schema_examples.py
from apps.favorites.schemas import FavoriteToggleResponse, FavoritesListResponse


def test_favorites_list_response_has_example():
    assert "example" in FavoritesListResponse.model_json_schema()


def test_favorite_toggle_response_has_example():
    assert "example" in FavoriteToggleResponse.model_json_schema()
```

- [ ] **Step 2: Убедиться, что тесты падают**

```bash
pytest apps/favorites/tests/test_schema_examples.py -v
```
Ожидаем: 2 FAILED

- [ ] **Step 3: Добавить примеры в favorites/schemas.py**

Добавить `from pydantic import ConfigDict` в импорты.

```python
class FavoritesListResponse(Schema):
    model_config = ConfigDict(json_schema_extra={"example": {
        "items": [
            {
                "id": 42,
                "title": "Перфоратор Bosch GBH 2-28",
                "description": "Мощный перфоратор, 880 Вт",
                "price": 12500,
                "category": [{"title": "Перфораторы", "slug": "perforatory"}],
                "sku": "BOSCH-GBH228",
                "status": {"slugStatus": "inStock", "title": "В наличии"},
                "poster": {
                    "original": {"src": "/media/products/bosch-gbh228.jpg", "mobile": None},
                    "webp": None, "avif": None,
                },
            }
        ],
        "total": 1,
    }})

    items: List[FavoriteProductCard]
    total: int


class FavoriteToggleResponse(Schema):
    model_config = ConfigDict(json_schema_extra={"example": {
        "is_favorite": True,
        "total": 5,
    }})

    is_favorite: bool
    total: int
```

- [ ] **Step 4: Запустить тесты**

```bash
pytest apps/favorites/tests/test_schema_examples.py -v
```
Ожидаем: 2 PASSED

- [ ] **Step 5: Коммит**

```bash
git add apps/favorites/schemas.py apps/favorites/tests/test_schema_examples.py
git commit -m "feat: добавить примеры ответов в favorites/schemas"
```

---

### Task 7: pages/schemas — HomePageOut, BannerPageOut, FeedbackPageOut, LegalDocumentOut

**Files:**
- Modify: `apps/pages/schemas.py`
- Test: `apps/pages/tests/test_schema_examples.py` (создать, если нет директории tests — создать `__init__.py`)

- [ ] **Step 1: Создать директорию тестов если не существует**

```bash
ls apps/pages/tests/ 2>/dev/null || (mkdir -p apps/pages/tests && touch apps/pages/tests/__init__.py)
```

- [ ] **Step 2: Написать тест**

```python
# apps/pages/tests/test_schema_examples.py
from apps.pages.schemas import BannerPageOut, FeedbackPageOut, HomePageOut, LegalDocumentOut


def test_home_page_out_has_example():
    assert "example" in HomePageOut.model_json_schema()


def test_banner_page_out_has_example():
    assert "example" in BannerPageOut.model_json_schema()


def test_feedback_page_out_has_example():
    assert "example" in FeedbackPageOut.model_json_schema()


def test_legal_document_out_has_example():
    assert "example" in LegalDocumentOut.model_json_schema()
```

- [ ] **Step 3: Убедиться, что тесты падают**

```bash
pytest apps/pages/tests/test_schema_examples.py -v
```
Ожидаем: 4 FAILED

- [ ] **Step 4: Добавить примеры в pages/schemas.py**

Добавить `from pydantic import ConfigDict` в импорты.

```python
class HomePageOut(Schema):
    model_config = ConfigDict(json_schema_extra={"example": {
        "hero": {
            "title": "Профессиональные инструменты с доставкой",
            "description": "Широкий выбор строительных инструментов от ведущих мировых производителей",
            "button": {"title": "Перейти в каталог", "href": "/catalog"},
            "poster": {"original": {"src": "/media/pages/hero-bg.jpg", "mobile": None}, "webp": None, "avif": None},
        },
        "about_company": {
            "title": "О компании",
            "content": "<p>Мы поставляем инструменты с 2010 года...</p>",
            "poster": None,
        },
        "reviews": {
            "title": "Отзывы покупателей",
            "reviews": [
                {
                    "title": "Отличный инструмент!",
                    "description": "Купил перфоратор, очень доволен качеством.",
                    "grade": 5,
                    "author": {"fullName": "Алексей Смирнов", "icon": None},
                }
            ],
        },
        "showcase": None,
        "news_cta": None,
    }})

    hero: Optional[HomeHero] = None
    about_company: Optional[HomeAbout] = None
    reviews: Optional[HomeReviews] = None
    showcase: Optional[HomeShowcase] = None
    news_cta: Optional[HomeNewsCTA] = None


class BannerPageOut(Schema):
    model_config = ConfigDict(json_schema_extra={"example": {
        "banner": {
            "title": "О компании",
            "description": "Интернет-магазин профессионального инструмента с 2010 года",
            "poster": {"original": {"src": "/media/pages/about-banner.jpg", "mobile": None}, "webp": None, "avif": None},
        },
        "content": "<p>Мы специализируемся на продаже профессионального инструмента...</p>",
    }})

    banner: Optional[BannerWithoutButton] = None
    content: Optional[str] = None


class FeedbackPageOut(Schema):
    model_config = ConfigDict(json_schema_extra={"example": {
        "section": {
            "title": "Обратная связь",
            "description": "Оставьте заявку и мы свяжемся с вами в течение рабочего дня",
        },
        "news_cta": {
            "title": "Читайте наш блог",
            "description": "Обзоры, советы и новости мира инструментов",
            "button": {"title": "Перейти в новости", "href": "/news"},
            "poster": None,
        },
    }})

    section: Optional[FeedbackSection] = None
    news_cta: Optional[HomeNewsCTA] = None


class LegalDocumentOut(Schema):
    model_config = ConfigDict(json_schema_extra={"example": {
        "title": "Политика конфиденциальности",
        "last_updated": "2024-09-01",
        "sections": [
            {
                "id": "general",
                "title": "1. Общие положения",
                "content": "<p>Настоящая политика определяет порядок обработки персональных данных...</p>",
            },
            {
                "id": "data-collection",
                "title": "2. Сбор данных",
                "content": "<p>Мы собираем данные, которые вы предоставляете при регистрации...</p>",
            },
        ],
    }})

    title: str
    last_updated: str
    sections: List[LegalSectionOut]
```

- [ ] **Step 5: Запустить тесты**

```bash
pytest apps/pages/tests/test_schema_examples.py -v
```
Ожидаем: 4 PASSED

- [ ] **Step 6: Коммит**

```bash
git add apps/pages/schemas.py apps/pages/tests/
git commit -m "feat: добавить примеры ответов в pages/schemas"
```

---

### Task 8: feedback/schemas — FeedbackSubmitResponse

**Files:**
- Modify: `apps/feedback/schemas.py`
- Test: `apps/feedback/tests/test_schema_examples.py` (создать)

- [ ] **Step 1: Написать тест**

```python
# apps/feedback/tests/test_schema_examples.py
from apps.feedback.schemas import FeedbackSubmitResponse


def test_feedback_submit_response_has_example():
    assert "example" in FeedbackSubmitResponse.model_json_schema()
```

- [ ] **Step 2: Убедиться, что тест падает**

```bash
pytest apps/feedback/tests/test_schema_examples.py -v
```
Ожидаем: 1 FAILED

- [ ] **Step 3: Добавить пример в feedback/schemas.py**

Добавить `from pydantic import ConfigDict` в импорты файла.

```python
class FeedbackSubmitResponse(Schema):
    model_config = ConfigDict(json_schema_extra={"example": {
        "id": 88,
        "message": "Спасибо! Ваше обращение принято. Мы свяжемся с вами в ближайшее время.",
    }})

    id: int
    message: str
```

- [ ] **Step 4: Запустить тест**

```bash
pytest apps/feedback/tests/test_schema_examples.py -v
```
Ожидаем: 1 PASSED

- [ ] **Step 5: Коммит**

```bash
git add apps/feedback/schemas.py apps/feedback/tests/test_schema_examples.py
git commit -m "feat: добавить примеры ответов в feedback/schemas"
```

---

### Task 9: Итоговая проверка — все тесты и OpenAPI

**Files:** нет изменений

- [ ] **Step 1: Запустить все новые тесты разом**

```bash
pytest apps/users/tests/test_schema_examples.py \
       apps/products/tests/test_schema_examples.py \
       apps/products/tests/test_catalog_schema_examples.py \
       apps/orders/tests/test_schema_examples.py \
       apps/news/tests/test_schema_examples.py \
       apps/favorites/tests/test_schema_examples.py \
       apps/pages/tests/test_schema_examples.py \
       apps/feedback/tests/test_schema_examples.py \
       -v
```
Ожидаем: все PASSED, 0 failed

- [ ] **Step 2: Запустить полный тест-сьют чтобы убедиться в отсутствии регрессий**

```bash
pytest --tb=short -q
```
Ожидаем: все существующие тесты PASSED

- [ ] **Step 3: Финальный коммит (если нужен)**

Если всё прошло — завершение задачи. Если нет — проверить вывод ошибок и исправить конкретный файл.

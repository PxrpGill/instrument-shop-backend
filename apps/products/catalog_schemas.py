"""Pydantic-схемы публичного каталога по контракту contracts/catalog/*.

Имена полей соответствуют JSON-контракту 1-в-1, включая опечатку
`techicalSpecifications` (см. примечание в `contracts/shared/product.json`:
менять нельзя — типизация фронта зависит).

Все поля, помеченные `Optional[...] = None`, при отсутствии данных не
включаются в JSON-ответ контроллером (см. README §«Опциональные поля
не возвращаются, а не null»).
"""

from __future__ import annotations

from typing import List, Literal, Optional

from ninja import Schema
from pydantic import ConfigDict

from apps.shared.schemas import PaginationMeta, PictureSchema, SiteLink

# ---------------------------------------------------------------------------
# Базовые блоки
# ---------------------------------------------------------------------------


class ProductCategory(Schema):
    """Минимальная категория, используется в фильтрах и карточках товара."""

    title: str
    slug: str


class ProductStatus(Schema):
    """Статус карточки. slugStatus только inStock | outOfStock."""

    slugStatus: Literal["inStock", "outOfStock"]
    title: str


class TechSpecificationRow(Schema):
    label: str
    value: str


class TechSpecificationGroup(Schema):
    title: str
    specifications: List[TechSpecificationRow]


class DescriptionParametersGroup(Schema):
    title: str
    parameters: str  # HTML


# ---------------------------------------------------------------------------
# shared/product — listing vs detail
# ---------------------------------------------------------------------------


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


# ---------------------------------------------------------------------------
# Блоки страниц
# ---------------------------------------------------------------------------


class CategoriesBlock(Schema):
    title: str
    categories: List[ProductCategory]


class PriceFilter(Schema):
    start_range: int
    end_range: int


class CategoriesFilter(Schema):
    categories: List[ProductCategory]


class CatalogFilterBlock(Schema):
    price_filter: PriceFilter
    categories_filter: CategoriesFilter


class CategoryFilterBlock(Schema):
    price_filter: PriceFilter


class ProductsBlock(Schema):
    title: str
    products: List[ProductListItem]
    meta: PaginationMeta


class ShowcaseGroup(Schema):
    title: str
    products: List[ProductListItem]


class ShowcaseBlock(Schema):
    title: str
    button: SiteLink
    showcases: List[ShowcaseGroup]


# ---------------------------------------------------------------------------
# Корневые ответы
# ---------------------------------------------------------------------------


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

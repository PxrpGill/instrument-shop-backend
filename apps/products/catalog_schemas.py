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

    categories_block: CategoriesBlock
    filter_block: CatalogFilterBlock
    products_block: ProductsBlock


class CategoryResponse(Schema):
    """GET /catalog/categories/{slug} — страница категории."""

    category: ProductCategory
    filter_block: CategoryFilterBlock
    products_block: ProductsBlock


class ProductDetailResponse(Schema):
    """GET /catalog/products/{id} — карточка товара."""

    product: ProductDetail
    showcase: Optional[ShowcaseBlock] = None

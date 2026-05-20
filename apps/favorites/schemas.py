"""Pydantic-схемы модуля «Избранное».

Соответствуют контрактам:
- contracts/favorites/list.json — listing-формат shared/product + total.
- contracts/favorites/toggle.json — {is_favorite, total} для POST.
"""

from __future__ import annotations

from typing import List, Optional

from ninja import Schema
from pydantic import ConfigDict

from apps.shared.schemas import PictureSchema


class ProductCategoryOut(Schema):
    """Категория товара в карточке shared/product."""

    title: str
    slug: str


class ProductStatusOut(Schema):
    """Статус наличия товара (опционален в листинге)."""

    slugStatus: str
    title: str


class FavoriteProductCard(Schema):
    """Карточка товара shared/product (listing-формат)."""

    id: int
    title: str
    description: str
    price: int
    category: List[ProductCategoryOut]
    sku: Optional[str] = None
    status: Optional[ProductStatusOut] = None
    poster: Optional[PictureSchema] = None


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

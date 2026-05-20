"""Pydantic-схемы модуля «Избранное».

Соответствуют контрактам:
- contracts/favorites/list.json — listing-формат shared/product + total.
- contracts/favorites/toggle.json — {is_favorite, total} для POST.
"""

from __future__ import annotations

from typing import List, Optional

from ninja import Schema

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
    items: List[FavoriteProductCard]
    total: int


class FavoriteToggleResponse(Schema):
    is_favorite: bool
    total: int

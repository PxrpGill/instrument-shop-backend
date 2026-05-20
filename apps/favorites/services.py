"""Бизнес-логика модуля «Избранное».

Идемпотентность toggle:
- POST уже существующего → возвращаем существующую запись, статус 200.
- DELETE отсутствующего → no-op, статус 204.
- 404 — только если product_id отсутствует в БД (а не «не в избранном»).

В list возвращаем только опубликованные товары — если товар архивирован/в черновике,
он остаётся в БД, но в выдачу не попадает.
"""

from __future__ import annotations

from typing import List, Optional

from django.db.models import Prefetch, QuerySet
from django.http import HttpRequest

from apps.products.catalog_serializers import serialize_product_list_item
from apps.products.models import Product, ProductImage, ProductStatusChoices
from apps.shared.errors import not_found
from apps.users.models import Customer

from .models import Favorite


def _product_exists(product_id: int) -> bool:
    return Product.objects.filter(pk=product_id).exists()


def _favorites_count(customer: Customer) -> int:
    return Favorite.objects.filter(customer=customer).count()


def add_favorite(customer: Customer, product_id: int) -> dict:
    """Добавить товар в избранное. Идемпотентно: повторный вызов не создаёт дубль."""
    if not _product_exists(product_id):
        raise not_found("Товар не найден")

    Favorite.objects.get_or_create(customer=customer, product_id=product_id)
    return {"is_favorite": True, "total": _favorites_count(customer)}


def remove_favorite(customer: Customer, product_id: int) -> None:
    """Удалить товар из избранного. Идемпотентно: повторный DELETE — no-op.

    404 поднимаем только если product_id не существует в БД.
    """
    if not _product_exists(product_id):
        raise not_found("Товар не найден")

    Favorite.objects.filter(customer=customer, product_id=product_id).delete()


def _favorite_products_queryset(customer: Customer) -> QuerySet[Product]:
    """Опубликованные товары из избранного с prefetched связями для карточки."""
    image_qs = ProductImage.objects.select_related("image").order_by(
        "-is_primary", "order", "created_at"
    )
    favorite_product_ids = Favorite.objects.filter(customer=customer).values_list(
        "product_id", flat=True
    )
    return (
        Product.objects.filter(
            pk__in=favorite_product_ids,
            status=ProductStatusChoices.PUBLISHED,
        )
        .prefetch_related("categories", Prefetch("images", queryset=image_qs))
        .order_by("-favorited_by__created_at")
    )


def list_favorites(
    customer: Customer, request: Optional[HttpRequest] = None
) -> dict:
    """Собрать ответ для GET /api/favorites."""
    products: List[Product] = list(_favorite_products_queryset(customer))
    items = [serialize_product_list_item(p, request) for p in products]
    return {"items": items, "total": len(items)}

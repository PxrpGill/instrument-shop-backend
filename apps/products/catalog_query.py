"""Фильтрация, сортировка, пагинация публичного каталога.

Тонкий слой над QuerySet, изолирующий от контроллера. Контроллер делает:

    products_qs = published_products()
    products_qs = apply_catalog_filters(products_qs, filters)
    products_qs = apply_sort(products_qs, sort)
    items, meta = paginate(products_qs, page, per_page, max_per_page=MAX_PER_PAGE)
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Iterable, List, Optional

from django.db.models import Max, Min, Prefetch, QuerySet

from apps.shared.utils.pagination import paginate as _paginate

from .models import Category, Product, ProductImage, ProductStatusChoices

DEFAULT_PER_PAGE = 24
MAX_PER_PAGE = 100

SORT_POPULAR = "popular"
SORT_PRICE_ASC = "price_asc"
SORT_PRICE_DESC = "price_desc"
SORT_NEW = "new"
ALLOWED_SORTS = {SORT_POPULAR, SORT_PRICE_ASC, SORT_PRICE_DESC, SORT_NEW}


@dataclass
class CatalogFilters:
    """Набор фильтров публичного каталога."""

    category_slugs: Optional[List[str]] = None
    price_min: Optional[int] = None
    price_max: Optional[int] = None


def published_products() -> QuerySet[Product]:
    """Базовый QuerySet опубликованных товаров с prefetched связями."""
    image_qs = ProductImage.objects.select_related("image").order_by(
        "-is_primary", "order", "created_at"
    )
    return Product.objects.filter(
        status=ProductStatusChoices.PUBLISHED
    ).prefetch_related("categories", Prefetch("images", queryset=image_qs))


def apply_catalog_filters(
    qs: QuerySet[Product], filters: CatalogFilters
) -> QuerySet[Product]:
    """Применить фильтры каталога к QuerySet."""
    if filters.category_slugs:
        qs = qs.filter(categories__slug__in=filters.category_slugs)
    if filters.price_min is not None:
        qs = qs.filter(price__gte=Decimal(filters.price_min))
    if filters.price_max is not None:
        qs = qs.filter(price__lte=Decimal(filters.price_max))
    return qs.distinct()


def apply_sort(qs: QuerySet[Product], sort: Optional[str]) -> QuerySet[Product]:
    """Применить сортировку. Неизвестное значение → 'popular' (fallback)."""
    if sort == SORT_PRICE_ASC:
        return qs.order_by("price", "-created_at")
    if sort == SORT_PRICE_DESC:
        return qs.order_by("-price", "-created_at")
    if sort == SORT_NEW:
        return qs.order_by("-created_at")
    # popular пока без отдельной метрики — fallback на -created_at.
    return qs.order_by("-created_at")


def compute_price_range(qs: QuerySet[Product]) -> tuple[int, int]:
    """Минимальная и максимальная цена в QuerySet (для слайдера фильтра).

    Возвращает (0, 0), если в выборке нет товаров с ценой.
    """
    agg = qs.aggregate(min_price=Min("price"), max_price=Max("price"))
    lo = agg["min_price"]
    hi = agg["max_price"]
    if lo is None or hi is None:
        return 0, 0
    return int(lo), int(hi)


def paginate_products(qs: QuerySet[Product], page: int, per_page: int):
    """Пагинация с лимитами каталога."""
    return _paginate(qs, page=page, per_page=per_page, max_per_page=MAX_PER_PAGE)


def list_visible_categories() -> Iterable[Category]:
    """Все категории — для блоков «плитки» и «чекбоксы фильтра»."""
    return Category.objects.all().order_by("name")


def showcase_for_product(product: Product, limit: int = 8) -> dict:
    """Подобрать товары «Рекомендуем» для product detail.

    Группирует по категориям текущего товара. Каждая группа — до `limit`
    других опубликованных товаров из этой категории. Группа без товаров
    в результат не попадает.
    """
    showcases: list[dict] = []
    for category in product.categories.all():
        items = list(
            published_products()
            .filter(categories=category)
            .exclude(pk=product.pk)
            .order_by("-created_at")[:limit]
        )
        if items:
            showcases.append({"category": category, "products": items})
    return {"showcases": showcases}

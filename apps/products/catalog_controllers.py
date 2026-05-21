"""Публичный каталог по контракту contracts/catalog/*.

Эндпоинты:
- GET /catalog                       — главная (категории + фильтры + товары)
- GET /catalog/categories/{slug}     — страница категории
- GET /catalog/products/{id}         — карточка товара

Аутентификация не требуется. На все эндпоинты включён rate limit и кеш.
"""

from typing import List, Optional

from django.core.cache import cache
from django.http import HttpRequest
from django.shortcuts import get_object_or_404
from django_ratelimit.decorators import ratelimit
from ninja import Query, Router

from apps.shared.errors import BusinessError, not_found

from . import catalog_query as cq
from .catalog_serializers import (serialize_categories, serialize_category,
                                  serialize_product_detail,
                                  serialize_product_list)
from .models import Category, Product, ProductStatusChoices

router = Router(tags=["Catalog"])

# ---------------------------------------------------------------------------
# Кеш-ключи и TTL
# ---------------------------------------------------------------------------

CACHE_TTL_LIST = 60  # 1 минута на листинги
CACHE_TTL_DETAIL = 300  # 5 минут на карточку товара

CATALOG_KEY_PREFIX = "catalog"


def _make_catalog_key(params) -> str:
    """Стабильный ключ кеша по query-параметрам."""
    serialized = "&".join(f"{k}={v}" for k, v in params)
    return f"{CATALOG_KEY_PREFIX}:root:{serialized or 'default'}"


def _make_category_key(slug: str, params) -> str:
    serialized = "&".join(f"{k}={v}" for k, v in params)
    return f"{CATALOG_KEY_PREFIX}:category:{slug}:{serialized or 'default'}"


def _make_product_key(product_id: int) -> str:
    return f"{CATALOG_KEY_PREFIX}:product:{product_id}"


# ---------------------------------------------------------------------------
# Парсинг query
# ---------------------------------------------------------------------------


def _parse_category_slugs(raw: Optional[List[str]]) -> Optional[List[str]]:
    if not raw:
        return None
    # `?categories=a&categories=b` приходит как list[str]; пустые отбрасываем.
    cleaned = [s for s in raw if s]
    return cleaned or None


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.get("")
@ratelimit(key="ip", rate="100/m", method="GET", block=True)
def get_catalog(
    request: HttpRequest,
    page: int = Query(1, ge=1),
    per_page: int = Query(cq.DEFAULT_PER_PAGE, ge=1, le=cq.MAX_PER_PAGE),
    price_min: Optional[int] = Query(None, ge=0),
    price_max: Optional[int] = Query(None, ge=0),
    categories: Optional[List[str]] = Query(None),
    sort: Optional[str] = Query(cq.SORT_POPULAR),
):
    """Главная каталога: плитки категорий, фильтры и пагинированный список."""
    params = sorted(request.GET.items())
    cache_key = _make_catalog_key(params)
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    filters = cq.CatalogFilters(
        category_slugs=_parse_category_slugs(categories),
        price_min=price_min,
        price_max=price_max,
    )

    all_categories = list(cq.list_visible_categories())

    # Цена считается по всему каталогу без учёта текущих фильтров.
    all_published = cq.published_products()
    start_range, end_range = cq.compute_price_range(all_published)

    filtered = cq.apply_catalog_filters(all_published, filters)
    sorted_qs = cq.apply_sort(filtered, sort)
    items, meta = cq.paginate_products(sorted_qs, page=page, per_page=per_page)

    payload = {
        "categories_block": {
            "title": "Категории инструментов",
            "categories": serialize_categories(all_categories),
        },
        "filter_block": {
            "price_filter": {"start_range": start_range, "end_range": end_range},
            "categories_filter": {
                "categories": serialize_categories(all_categories),
            },
        },
        "products_block": {
            "title": "Товары",
            "products": serialize_product_list(items, request),
            "meta": meta,
        },
    }
    cache.set(cache_key, payload, CACHE_TTL_LIST)
    return payload


@router.get("/categories/{slug}")
@ratelimit(key="ip", rate="100/m", method="GET", block=True)
def get_category(
    request: HttpRequest,
    slug: str,
    page: int = Query(1, ge=1),
    per_page: int = Query(cq.DEFAULT_PER_PAGE, ge=1, le=cq.MAX_PER_PAGE),
    price_min: Optional[int] = Query(None, ge=0),
    price_max: Optional[int] = Query(None, ge=0),
    sort: Optional[str] = Query(cq.SORT_POPULAR),
):
    """Страница одной категории: фильтр цены + товары этой категории."""
    try:
        category = Category.objects.get(slug=slug)
    except Category.DoesNotExist as exc:
        raise not_found("Категория не найдена") from exc

    params = sorted(request.GET.items())
    cache_key = _make_category_key(slug, params)
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    base_qs = cq.published_products().filter(categories=category).distinct()

    # Диапазон цен — по всем товарам категории, без учёта текущего фильтра цены.
    start_range, end_range = cq.compute_price_range(base_qs)

    filtered = cq.apply_catalog_filters(
        base_qs,
        cq.CatalogFilters(price_min=price_min, price_max=price_max),
    )
    sorted_qs = cq.apply_sort(filtered, sort)
    items, meta = cq.paginate_products(sorted_qs, page=page, per_page=per_page)

    payload = {
        "category": serialize_category(category),
        "filter_block": {
            "price_filter": {"start_range": start_range, "end_range": end_range},
        },
        "products_block": {
            "title": category.name,
            "products": serialize_product_list(items, request),
            "meta": meta,
        },
    }
    cache.set(cache_key, payload, CACHE_TTL_LIST)
    return payload


@router.get("/products/{product_id}")
@ratelimit(key="ip", rate="100/m", method="GET", block=True)
def get_product_detail(request: HttpRequest, product_id: int):
    """Карточка одного товара + showcase «Рекомендуем»."""
    cache_key = _make_product_key(product_id)
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    try:
        product = cq.published_products().get(pk=product_id)
    except Product.DoesNotExist as exc:
        raise not_found("Товар не найден") from exc

    showcase = _build_showcase(product, request)

    payload = {
        "product": serialize_product_detail(product, request),
    }
    if showcase is not None:
        payload["showcase"] = showcase

    cache.set(cache_key, payload, CACHE_TTL_DETAIL)
    return payload


def _build_showcase(product: Product, request: HttpRequest) -> Optional[dict]:
    """Сформировать блок showcase «Рекомендуем» из соседних товаров."""
    data = cq.showcase_for_product(product, limit=8)
    groups = data["showcases"]
    if not groups:
        return None
    return {
        "title": "Рекомендуем",
        "button": {"title": "В каталог", "href": "/catalog"},
        "showcases": [
            {
                "title": group["category"].name,
                "products": serialize_product_list(group["products"], request),
            }
            for group in groups
        ],
    }


# ---------------------------------------------------------------------------
# Cache invalidation API
# ---------------------------------------------------------------------------


def invalidate_catalog_cache() -> None:
    """Сбросить весь кеш каталога (root + category + product)."""
    try:
        from django_redis import get_redis_connection

        redis_client = get_redis_connection("default")
        for key in redis_client.keys(f"instrument_shop:{CATALOG_KEY_PREFIX}:*"):
            redis_client.delete(key)
    except Exception:
        # Если Redis недоступен / не поддерживает keys — пропускаем; кеш истечёт сам.
        pass


def invalidate_product_cache(product_id: int) -> None:
    """Сбросить кеш одного товара (точечная инвалидация после публикации/правки)."""
    try:
        cache.delete(_make_product_key(product_id))
    except Exception:
        pass


# Сохраняем ссылку, чтобы при необходимости можно было передать через DI.
__all__ = [
    "router",
    "invalidate_catalog_cache",
    "invalidate_product_cache",
    "BusinessError",
]

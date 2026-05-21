"""Сериализаторы Product → dict по контракту contracts/shared/product.

Возвращаем чистые dict (а не Pydantic-экземпляры) с двумя ключевыми правилами
контракта:

1. price отдаём как целое (рубли) — Decimal → int.
2. Опциональные поля без значения в JSON **не появляются** (а не `null`).
   Поэтому ключи добавляются условно через if.
"""

from __future__ import annotations

from typing import Iterable, Optional

from django.http import HttpRequest

from apps.shared.services.picture import image_to_picture

from .models import Category, Product, ProductAvailabilityChoices

# Маппинг availability → slugStatus (контракт даёт только две опции).
_SLUG_STATUS_BY_AVAILABILITY = {
    ProductAvailabilityChoices.IN_STOCK: "inStock",
    ProductAvailabilityChoices.OUT_OF_STOCK: "outOfStock",
    ProductAvailabilityChoices.ON_REQUEST: "inStock",
}


def serialize_category(category: Category) -> dict:
    """Категория в формате shared/product-category (минимальный — title+slug)."""
    return {"title": category.name, "slug": category.slug}


def serialize_categories(categories: Iterable[Category]) -> list[dict]:
    return [serialize_category(c) for c in categories]


def serialize_status(product: Product) -> dict:
    """status: {slugStatus, title} — обязателен в detail, опционален в listing."""
    availability = product.availability
    slug = _SLUG_STATUS_BY_AVAILABILITY.get(availability, "outOfStock")
    title = product.get_availability_display()
    return {"slugStatus": slug, "title": title}


def _poster_picture(product: Product, request: Optional[HttpRequest]) -> Optional[dict]:
    """Главное фото товара → shared/picture. None, если фото нет."""
    primary = None
    for product_image in product.images.all():
        if product_image.is_primary:
            primary = product_image
            break
    if primary is None:
        # Берём первое по сортировке (-is_primary, order, created_at).
        primary_iter = iter(product.images.all())
        primary = next(primary_iter, None)
    if primary is None or primary.image is None:
        return None
    return image_to_picture(primary.image, request)


def _gallery_pictures(product: Product, request: Optional[HttpRequest]) -> list[dict]:
    """Все изображения товара → list[shared/picture]. Может быть пустым."""
    gallery: list[dict] = []
    for product_image in product.images.all():
        if product_image.image is None:
            continue
        picture = image_to_picture(product_image.image, request)
        if picture is not None:
            gallery.append(picture)
    return gallery


def _price_to_int(product: Product) -> int:
    """price → int рублей (контракт: 'Целое (рубли)')."""
    if product.price is None:
        return 0
    return int(product.price)


def serialize_product_list_item(
    product: Product, request: Optional[HttpRequest] = None
) -> dict:
    """Карточка товара в листинге — формат shared/product (example_list)."""
    item: dict = {
        "id": product.id,
        "title": product.name,
        "description": product.description or "",
        "price": _price_to_int(product),
        "category": serialize_categories(product.categories.all()),
        "status": serialize_status(product),
    }
    if product.sku:
        item["sku"] = product.sku
    poster = _poster_picture(product, request)
    if poster is not None:
        item["poster"] = poster
    return item


def serialize_product_list(
    products: Iterable[Product], request: Optional[HttpRequest] = None
) -> list[dict]:
    return [serialize_product_list_item(p, request) for p in products]


def serialize_product_detail(
    product: Product, request: Optional[HttpRequest] = None
) -> dict:
    """Полная карточка товара — формат shared/product (example_detail)."""
    detail: dict = {
        "id": product.id,
        "title": product.name,
        "description": product.description or "",
        "price": _price_to_int(product),
        "status": serialize_status(product),
        "category": serialize_categories(product.categories.all()),
    }
    if product.sku:
        detail["sku"] = product.sku

    gallery = _gallery_pictures(product, request)
    if gallery:
        detail["gallery"] = gallery

    description_parameters = _serialize_description_parameters(product)
    if description_parameters:
        detail["descriptionParameters"] = description_parameters

    technical_specifications = _serialize_technical_specifications(product)
    if technical_specifications:
        # Внимание: имя поля с опечаткой — этого требует контракт фронта.
        detail["techicalSpecifications"] = technical_specifications

    return detail


def _serialize_description_parameters(product) -> list[dict]:
    out: list[dict] = []
    for block in product.description_blocks.all():
        if not block.title or not block.content:
            continue
        out.append({"title": block.title, "parameters": block.content})
    return out


def _serialize_technical_specifications(product) -> list[dict]:
    out: list[dict] = []
    for group in product.spec_groups.all():
        rows: list[dict] = [
            {"label": item.label, "value": item.value}
            for item in group.spec_items.all()
            if item.label
        ]
        if group.title and rows:
            out.append({"title": group.title, "specifications": rows})
    return out

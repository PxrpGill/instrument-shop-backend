"""Переиспользуемые Pydantic-схемы.

Соответствуют контрактам в `contracts/shared/`:
- PictureSchema      → shared/picture.json
- SiteLink           → shared/site-link.json (используется неявно через {title, href})
- PaginationMeta     → shared/pagination.json
"""

from __future__ import annotations

from typing import Optional

from ninja import Schema


class PictureVariant(Schema):
    """Один формат изображения. Может содержать desktop (src) и mobile варианты.

    Оба поля опциональны. Если ни одного нет, ключ формата (например, "avif")
    в Picture не возвращается вовсе.
    """

    src: Optional[str] = None
    mobile: Optional[str] = None


class PictureSchema(Schema):
    """Контракт shared/picture: оригинал + производные форматы.

    Все три формата опциональны. Пока конверсия webp/avif не завершилась —
    возвращается только original; фронт корректно отрендерит через <picture>
    с fallback'ами.
    """

    original: Optional[PictureVariant] = None
    webp: Optional[PictureVariant] = None
    avif: Optional[PictureVariant] = None


class SiteLink(Schema):
    """Контракт shared/site-link: {title, href}. Кнопки CTA, навигация."""

    title: str
    href: str


class PaginationMeta(Schema):
    """Контракт shared/pagination."""

    page: int
    per_page: int
    total_pages: int
    total_items: int

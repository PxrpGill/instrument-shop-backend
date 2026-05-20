"""Пагинация по контракту shared/pagination.json."""

from __future__ import annotations

import math
from typing import Tuple

from django.db.models import QuerySet

DEFAULT_PER_PAGE = 12
MAX_PER_PAGE = 50


def paginate(
    queryset: QuerySet,
    page: int = 1,
    per_page: int = DEFAULT_PER_PAGE,
    max_per_page: int = MAX_PER_PAGE,
) -> Tuple[list, dict]:
    """Разбить queryset на страницу + сформировать meta-блок.

    Возвращает (items, meta), где meta совпадает с shared/pagination:
    {page, per_page, total_pages, total_items}.

    Контракт поведения:
    - page < 1 → нормализуется в 1.
    - per_page ограничен сверху max_per_page.
    - Если page > total_pages — возвращается пустой items, не 404.
      Эндпоинт сам решает, что делать с этим случаем.
    """
    page = max(int(page or 1), 1)
    per_page = max(min(int(per_page or DEFAULT_PER_PAGE), max_per_page), 1)

    total_items = queryset.count()
    total_pages = math.ceil(total_items / per_page) if total_items else 0

    offset = (page - 1) * per_page
    items = list(queryset[offset : offset + per_page])

    meta = {
        "page": page,
        "per_page": per_page,
        "total_pages": total_pages,
        "total_items": total_items,
    }
    return items, meta

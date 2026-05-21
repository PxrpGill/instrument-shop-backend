"""Pydantic-схемы модуля новостей.

Соответствуют контрактам:
- contracts/news/list.json
- contracts/news/single.json
- contracts/shared/news-card.json
"""

from __future__ import annotations

from typing import List, Optional

from ninja import Schema
from pydantic import ConfigDict

from apps.shared.schemas import PaginationMeta, PictureSchema


class NewsTabOut(Schema):
    """Элемент массива tabs в /api/news."""

    title: str
    slug: str


class NewsCardSchema(Schema):
    """shared/news-card — карточка для списка новостей."""

    title: str
    slug: str
    date: str
    description: Optional[str] = None
    poster: Optional[PictureSchema] = None


class NewsListResponse(Schema):
    model_config = ConfigDict(json_schema_extra={"example": {
        "title": "Новости",
        "description": "Актуальные новости и статьи об инструментах",
        "tabs": [
            {"title": "Все", "slug": "all"},
            {"title": "Обзоры", "slug": "reviews"},
            {"title": "Советы", "slug": "tips"},
        ],
        "current_slug_tab": "all",
        "items": [
            {
                "title": "Новые перфораторы Bosch 2025: обзор линейки",
                "slug": "bosch-perforatory-2025",
                "date": "2025-03-10",
                "description": "Разбираем обновлённую линейку профессиональных перфораторов",
                "poster": {
                    "original": {"src": "/media/news/bosch-2025.jpg", "mobile": None},
                    "webp": None, "avif": None,
                },
            }
        ],
        "meta": {"page": 1, "per_page": 9, "total_pages": 4, "total_items": 35},
    }})

    title: str
    description: str
    tabs: List[NewsTabOut]
    current_slug_tab: str
    items: List[NewsCardSchema]
    meta: PaginationMeta


class NewsSingleBanner(Schema):
    title: str
    description: Optional[str] = None
    poster: Optional[PictureSchema] = None


class NewsSingleResponse(Schema):
    model_config = ConfigDict(json_schema_extra={"example": {
        "banner": {
            "title": "Новые перфораторы Bosch 2025: обзор линейки",
            "description": "Разбираем обновлённую линейку профессиональных перфораторов Bosch",
            "poster": {
                "original": {"src": "/media/news/bosch-2025.jpg", "mobile": None},
                "webp": None, "avif": None,
            },
        },
        "content": "<p>В 2025 году Bosch представила обновлённую серию перфораторов...</p>",
        "date": "2025-03-10",
        "slug": "bosch-perforatory-2025",
    }})

    banner: NewsSingleBanner
    content: str
    date: str
    slug: str

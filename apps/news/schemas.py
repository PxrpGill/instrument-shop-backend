"""Pydantic-схемы модуля новостей.

Соответствуют контрактам:
- contracts/news/list.json
- contracts/news/single.json
- contracts/shared/news-card.json
"""

from __future__ import annotations

from typing import List, Optional

from ninja import Schema

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
    banner: NewsSingleBanner
    content: str
    date: str
    slug: str

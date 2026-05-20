"""Публичные эндпоинты модуля новостей.

Контракты:
- GET /api/news      → contracts/news/list.json
- GET /api/news/{slug} → contracts/news/single.json
"""

from __future__ import annotations

from django.http import HttpRequest
from ninja import Query, Router

from apps.shared.errors import not_found

from .services import (
    NEWS_PER_PAGE_DEFAULT,
    get_news_list,
    get_published_article,
    serialize_single,
)

router = Router(tags=["News"])


@router.get(
    "",
    description="Список новостей с фильтрацией по табу и пагинацией.",
    summary="Get news list",
)
def list_news(
    request: HttpRequest,
    tab: str = Query("all"),
    page: int = Query(1),
    per_page: int = Query(NEWS_PER_PAGE_DEFAULT),
):
    return get_news_list(
        tab_slug=tab,
        page=page,
        per_page=per_page,
        request=request,
    )


@router.get(
    "/{slug}",
    description="Страница одной новости.",
    summary="Get news article",
)
def get_news(request: HttpRequest, slug: str):
    article = get_published_article(slug)
    if article is None:
        raise not_found("Новость не найдена")
    return serialize_single(article, request)

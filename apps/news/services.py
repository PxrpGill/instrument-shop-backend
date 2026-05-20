"""Сервисы модуля новостей: фильтрация, пагинация, сериализация."""

from __future__ import annotations

from typing import Optional

from django.db.models import QuerySet
from django.http import HttpRequest

from apps.shared.services.picture import image_to_picture
from apps.shared.utils.pagination import paginate

from .models import (
    ALL_TAB_SLUG,
    ALL_TAB_TITLE,
    NewsArticle,
    NewsArticleStatus,
    NewsPageSettings,
    NewsTab,
)


NEWS_PER_PAGE_DEFAULT = 12
NEWS_PER_PAGE_MAX = 50


def _isoformat(dt) -> str:
    """ISO 8601 UTC с суффиксом Z (как в контрактах)."""
    if dt is None:
        return ""
    # Django хранит datetime в UTC при USE_TZ=True; нормализуем формат.
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def _published_queryset() -> QuerySet[NewsArticle]:
    return NewsArticle.objects.filter(status=NewsArticleStatus.PUBLISHED).select_related(
        "tab", "picture"
    )


def get_news_list(
    *,
    tab_slug: str,
    page: int,
    per_page: int,
    request: Optional[HttpRequest] = None,
) -> dict:
    """Собрать ответ для GET /api/news.

    `tab_slug` 'all' (или пусто) → без фильтра. Неизвестный slug → пустой items
    с meta.total_items=0 (200, как договорено в плане).
    """
    settings_obj = NewsPageSettings.get_solo()

    qs = _published_queryset()
    current_slug = tab_slug or ALL_TAB_SLUG
    if current_slug != ALL_TAB_SLUG:
        qs = qs.filter(tab__slug=current_slug)

    items_qs, meta = paginate(
        qs,
        page=page,
        per_page=per_page,
        max_per_page=NEWS_PER_PAGE_MAX,
    )

    return {
        "title": settings_obj.title or "",
        "description": settings_obj.description or "",
        "tabs": _serialize_tabs(),
        "current_slug_tab": current_slug,
        "items": [serialize_card(article, request) for article in items_qs],
        "meta": meta,
    }


def _serialize_tabs() -> list[dict]:
    """Все табы из админки + служебный 'all' первым."""
    tabs = [{"title": ALL_TAB_TITLE, "slug": ALL_TAB_SLUG}]
    for tab in NewsTab.objects.all().order_by("order", "title"):
        tabs.append({"title": tab.title, "slug": tab.slug})
    return tabs


def serialize_card(
    article: NewsArticle, request: Optional[HttpRequest] = None
) -> dict:
    """Контракт shared/news-card."""
    out: dict = {
        "title": article.title,
        "slug": article.slug,
        "date": _isoformat(article.date),
    }
    if article.description:
        out["description"] = article.description
    poster = image_to_picture(article.picture, request)
    if poster is not None:
        out["poster"] = poster
    return out


def serialize_single(
    article: NewsArticle, request: Optional[HttpRequest] = None
) -> dict:
    """Контракт contracts/news/single.json."""
    banner: dict = {"title": article.title}
    if article.description:
        banner["description"] = article.description
    poster = image_to_picture(article.picture, request)
    if poster is not None:
        banner["poster"] = poster

    return {
        "banner": banner,
        "content": article.content or "",
        "date": _isoformat(article.date),
        "slug": article.slug,
    }


def get_published_article(slug: str) -> NewsArticle | None:
    return (
        _published_queryset()
        .filter(slug=slug)
        .first()
    )

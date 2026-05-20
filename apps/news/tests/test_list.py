"""Тесты GET /api/news (список новостей с табами и пагинацией)."""

from __future__ import annotations

from datetime import timedelta

import pytest
from django.utils import timezone

from apps.news.models import (
    NewsArticle,
    NewsArticleStatus,
    NewsPageSettings,
    NewsTab,
)

pytestmark = pytest.mark.django_db


def test_empty_list_returns_meta_zero(client):
    response = client.get("/news?tab=all")
    assert response.status_code == 200
    data = response.json()
    assert data["current_slug_tab"] == "all"
    assert data["items"] == []
    assert data["meta"] == {
        "page": 1,
        "per_page": 12,
        "total_pages": 0,
        "total_items": 0,
    }
    # Служебный таб 'all' всегда первым.
    assert data["tabs"][0] == {"title": "Все новости", "slug": "all"}


def test_list_returns_page_settings(client):
    settings_obj = NewsPageSettings.get_solo()
    settings_obj.title = "Новости магазина"
    settings_obj.description = "Будьте в курсе"
    settings_obj.save()

    data = client.get("/news").json()
    assert data["title"] == "Новости магазина"
    assert data["description"] == "Будьте в курсе"


def test_list_includes_admin_tabs_after_all(client):
    NewsTab.objects.create(slug="sales", title="Акции", order=1)
    NewsTab.objects.create(slug="new", title="Новинки", order=2)

    data = client.get("/news").json()
    slugs = [t["slug"] for t in data["tabs"]]
    assert slugs == ["all", "sales", "new"]


def test_list_filters_only_published(client):
    NewsArticle.objects.create(
        title="Опубликованная",
        slug="published",
        status=NewsArticleStatus.PUBLISHED,
    )
    NewsArticle.objects.create(
        title="Черновик",
        slug="draft",
        status=NewsArticleStatus.DRAFT,
    )

    data = client.get("/news?tab=all").json()
    titles = [item["title"] for item in data["items"]]
    assert titles == ["Опубликованная"]
    assert data["meta"]["total_items"] == 1


def test_list_filters_by_tab(client):
    sales = NewsTab.objects.create(slug="sales", title="Акции")
    tips = NewsTab.objects.create(slug="tips", title="Советы")

    NewsArticle.objects.create(
        title="Скидка", slug="sale-1", status="published", tab=sales
    )
    NewsArticle.objects.create(
        title="Как выбрать", slug="tip-1", status="published", tab=tips
    )
    NewsArticle.objects.create(
        title="Без таба", slug="no-tab", status="published", tab=None
    )

    data = client.get("/news?tab=sales").json()
    assert data["current_slug_tab"] == "sales"
    titles = [item["title"] for item in data["items"]]
    assert titles == ["Скидка"]


def test_list_unknown_tab_returns_empty(client):
    NewsArticle.objects.create(
        title="A", slug="a", status="published",
    )
    data = client.get("/news?tab=unknown").json()
    assert data["current_slug_tab"] == "unknown"
    assert data["items"] == []
    assert data["meta"]["total_items"] == 0


def test_list_pagination_per_page_clamped(client):
    for i in range(5):
        NewsArticle.objects.create(
            title=f"N{i}", slug=f"n-{i}", status="published"
        )

    # per_page > 50 ограничивается до 50 в paginate().
    data = client.get("/news?per_page=999").json()
    assert data["meta"]["per_page"] == 50


def test_list_card_includes_optional_description(client):
    NewsArticle.objects.create(
        title="С тизером",
        slug="with-desc",
        status="published",
        description="Тизер",
    )
    NewsArticle.objects.create(
        title="Без тизера",
        slug="no-desc",
        status="published",
    )

    items = client.get("/news").json()["items"]
    by_slug = {i["slug"]: i for i in items}
    assert by_slug["with-desc"]["description"] == "Тизер"
    assert "description" not in by_slug["no-desc"]


def test_list_ordered_by_date_desc(client):
    older = timezone.now() - timedelta(days=3)
    newer = timezone.now() - timedelta(days=1)
    NewsArticle.objects.create(
        title="Старее", slug="older", status="published", date=older
    )
    NewsArticle.objects.create(
        title="Новее", slug="newer", status="published", date=newer
    )

    titles = [i["title"] for i in client.get("/news").json()["items"]]
    assert titles == ["Новее", "Старее"]


def test_list_default_per_page_is_12(client):
    data = client.get("/news").json()
    assert data["meta"]["per_page"] == 12

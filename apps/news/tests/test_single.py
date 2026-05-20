"""Тесты GET /api/news/{slug} (страница одной новости)."""

from __future__ import annotations

import pytest

from apps.news.models import NewsArticle, NewsArticleStatus

pytestmark = pytest.mark.django_db


def test_single_unknown_slug_404(client):
    response = client.get("/news/missing-slug")
    assert response.status_code == 404
    body = response.json()
    assert body["error"]["code"] == "NOT_FOUND"


def test_single_draft_returns_404(client):
    NewsArticle.objects.create(
        title="Черновик",
        slug="draft-article",
        status=NewsArticleStatus.DRAFT,
    )
    response = client.get("/news/draft-article")
    assert response.status_code == 404


def test_single_happy_path(client):
    NewsArticle.objects.create(
        title="Новая линейка садовой техники 2026",
        slug="new-garden-equipment-2026",
        description="В продажу поступили газонокосилки",
        content="<p>Текст</p>",
        status=NewsArticleStatus.PUBLISHED,
    )
    data = client.get("/news/new-garden-equipment-2026").json()

    assert data["slug"] == "new-garden-equipment-2026"
    assert data["banner"]["title"] == "Новая линейка садовой техники 2026"
    assert data["banner"]["description"] == "В продажу поступили газонокосилки"
    assert data["content"] == "<p>Текст</p>"
    # ISO 8601 UTC, заканчивается на 'Z'
    assert data["date"].endswith("Z")


def test_single_without_description_omits_field(client):
    NewsArticle.objects.create(
        title="Без тизера",
        slug="no-teaser",
        status=NewsArticleStatus.PUBLISHED,
        content="<p>Контент</p>",
    )
    data = client.get("/news/no-teaser").json()
    assert "description" not in data["banner"]
    assert "poster" not in data["banner"]


def test_single_sanitizes_content_on_save():
    article = NewsArticle.objects.create(
        title="X",
        slug="sanitize",
        status=NewsArticleStatus.PUBLISHED,
        content="<script>alert(1)</script><p>ok</p>",
    )
    article.refresh_from_db()
    assert "<script>" not in article.content
    assert "<p>ok</p>" in article.content

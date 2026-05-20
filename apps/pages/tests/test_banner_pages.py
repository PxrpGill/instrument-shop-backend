"""Тесты страниц «О компании» и «Покупателям» (структура banner + content)."""

from __future__ import annotations

import pytest

from apps.pages.models import AboutUsPage, BuyersPage

pytestmark = pytest.mark.django_db


@pytest.mark.parametrize(
    "url,model_cls",
    [
        ("/pages/about-us", AboutUsPage),
        ("/pages/buyers", BuyersPage),
    ],
)
def test_banner_page_empty(client, url, model_cls):
    response = client.get(url)
    assert response.status_code == 200
    assert response.json() == {}


@pytest.mark.parametrize(
    "url,model_cls",
    [
        ("/pages/about-us", AboutUsPage),
        ("/pages/buyers", BuyersPage),
    ],
)
def test_banner_page_filled(client, url, model_cls):
    page = model_cls.get_solo()
    page.banner_title = "О компании"
    page.banner_description = "Профессиональный инструмент"
    page.content = "<h2>История</h2><p>Текст</p>"
    page.save()

    data = client.get(url).json()
    assert data == {
        "banner": {
            "title": "О компании",
            "description": "Профессиональный инструмент",
        },
        "content": "<h2>История</h2><p>Текст</p>",
    }


def test_banner_page_only_content():
    """Если редактор задал только контент — баннер не возвращается."""
    page = AboutUsPage.get_solo()
    page.content = "<p>Только текст</p>"
    page.save()

    from ninja.testing import TestClient
    from instrument_shop.api import api

    data = TestClient(api).get("/pages/about-us").json()
    assert "banner" not in data
    assert data["content"] == "<p>Только текст</p>"


def test_banner_page_sanitizes_content(client):
    page = AboutUsPage.get_solo()
    page.content = "<script>x</script><h2>ok</h2>"
    page.save()
    page.refresh_from_db()
    assert "<script>" not in page.content
    assert "<h2>ok</h2>" in page.content

"""Тесты страницы обратной связи (/api/pages/feedback)."""

from __future__ import annotations

import pytest

from apps.pages.models import FeedbackPage

pytestmark = pytest.mark.django_db


def test_feedback_empty(client):
    response = client.get("/pages/feedback")
    assert response.status_code == 200
    assert response.json() == {}


def test_feedback_section_only(client):
    page = FeedbackPage.get_solo()
    page.section_title = "Возникли вопросы?"
    page.section_description = "Мы здесь, чтобы помочь."
    page.save()

    data = client.get("/pages/feedback").json()
    assert data == {
        "section": {
            "title": "Возникли вопросы?",
            "description": "Мы здесь, чтобы помочь.",
        }
    }


def test_feedback_full(client):
    page = FeedbackPage.get_solo()
    page.section_title = "Возникли вопросы?"
    page.section_description = "Описание"
    page.news_cta_title = "Жизнь магазина"
    page.news_cta_description = "Новости"
    page.news_cta_button_title = "Смотреть"
    page.news_cta_button_href = "/news"
    page.save()

    data = client.get("/pages/feedback").json()
    assert data["section"]["title"] == "Возникли вопросы?"
    assert data["news_cta"] == {
        "title": "Жизнь магазина",
        "description": "Новости",
        "button": {"title": "Смотреть", "href": "/news"},
    }

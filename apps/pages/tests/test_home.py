"""Тесты главной страницы (/api/pages/home).

Проверяем правила контракта contracts/pages/home.json:
- пустая страница: возвращается {} (нет ни одной заполненной секции);
- заполненная страница: все секции присутствуют 1-в-1 с example;
- опциональные секции отсутствуют (а не равны null), когда поля пусты;
- порядок отзывов / групп витрины / товаров в группах соблюдён.
"""

from __future__ import annotations

import pytest

from apps.pages.models import (
    HomePage,
    HomePageReview,
    HomePageShowcase,
    HomePageShowcaseProduct,
)
from apps.reviews.models import Review

pytestmark = pytest.mark.django_db


def test_home_empty_returns_empty_object(client):
    response = client.get("/pages/home")
    assert response.status_code == 200
    assert response.json() == {}


def test_home_hero_only(client):
    page = HomePage.get_solo()
    page.hero_title = "Инструменты"
    page.hero_description = "<p>Описание</p>"
    page.hero_button_title = "Купить"
    page.hero_button_href = "/catalog"
    page.save()

    data = client.get("/pages/home").json()

    assert data == {
        "hero": {
            "title": "Инструменты",
            "description": "<p>Описание</p>",
            "button": {"title": "Купить", "href": "/catalog"},
        }
    }
    # Опциональные ключи отсутствуют, а не равны null.
    assert "about_company" not in data
    assert "reviews" not in data
    assert "showcase" not in data
    assert "news_cta" not in data


def test_home_reviews_section_orders_and_filters(client):
    page = HomePage.get_solo()
    page.reviews_title = "Отзывы"
    page.save()

    r1 = Review.objects.create(
        title="A", description="d", grade=5, author_full_name="Анна"
    )
    r2 = Review.objects.create(
        title="B", description="d", grade=4, author_full_name="Борис"
    )
    r_hidden = Review.objects.create(
        title="Скрытый",
        description="d",
        grade=1,
        author_full_name="C",
        is_published=False,
    )

    HomePageReview.objects.create(home_page=page, review=r2, order=10)
    HomePageReview.objects.create(home_page=page, review=r1, order=5)
    HomePageReview.objects.create(home_page=page, review=r_hidden, order=1)

    data = client.get("/pages/home").json()

    assert data["reviews"]["title"] == "Отзывы"
    titles = [item["title"] for item in data["reviews"]["reviews"]]
    assert titles == ["A", "B"]  # r1.order=5 раньше r2.order=10; r_hidden отфильтрован
    assert data["reviews"]["reviews"][0]["author"] == {"fullName": "Анна"}
    assert data["reviews"]["reviews"][0]["grade"] == 5


def test_home_showcase_groups_and_products_ordered(client, product_factory):
    page = HomePage.get_solo()
    page.showcase_title = "Наши товары"
    page.showcase_button_title = "В каталог"
    page.showcase_button_href = "/catalog"
    page.save()

    g_second = HomePageShowcase.objects.create(
        home_page=page, title="Электроинструмент", order=2
    )
    g_first = HomePageShowcase.objects.create(
        home_page=page, title="Ручной инструмент", order=1
    )

    p1 = product_factory(name="Молоток", price=100, status="published")
    p2 = product_factory(name="Дрель", price=500, status="published")
    p3 = product_factory(name="Шуруповёрт", price=700, status="published")

    HomePageShowcaseProduct.objects.create(showcase=g_first, product=p1, order=0)
    HomePageShowcaseProduct.objects.create(showcase=g_second, product=p3, order=1)
    HomePageShowcaseProduct.objects.create(showcase=g_second, product=p2, order=0)

    data = client.get("/pages/home").json()

    showcase = data["showcase"]
    assert showcase["title"] == "Наши товары"
    assert showcase["button"] == {"title": "В каталог", "href": "/catalog"}
    assert [g["title"] for g in showcase["showcases"]] == [
        "Ручной инструмент",
        "Электроинструмент",
    ]
    second_group_products = [p["title"] for p in showcase["showcases"][1]["products"]]
    assert second_group_products == ["Дрель", "Шуруповёрт"]  # order=0 раньше order=1


def test_home_news_cta_section(client):
    page = HomePage.get_solo()
    page.news_cta_title = "Жизнь магазина"
    page.news_cta_description = "Новости"
    page.news_cta_button_title = "Смотреть"
    page.news_cta_button_href = "/news"
    page.save()

    data = client.get("/pages/home").json()

    assert data["news_cta"] == {
        "title": "Жизнь магазина",
        "description": "Новости",
        "button": {"title": "Смотреть", "href": "/news"},
    }


def test_home_sanitizes_html_on_save():
    page = HomePage.get_solo()
    page.hero_title = "X"
    page.hero_description = "<script>alert(1)</script><p>ok</p>"
    page.about_content = "<iframe src='evil'></iframe><h2>Hi</h2>"
    page.save()
    page.refresh_from_db()
    assert "<script>" not in page.hero_description
    assert "<p>ok</p>" in page.hero_description
    assert "<iframe" not in page.about_content
    assert "<h2>Hi</h2>" in page.about_content

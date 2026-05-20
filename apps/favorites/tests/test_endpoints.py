"""Тесты эндпоинтов /api/favorites/*.

Покрытие:
- 401 без токена на каждом эндпоинте.
- GET список: пустой → пустой items; непустой → товары в listing-формате,
  архивированные товары исключаются.
- POST happy + повторный POST (идемпотентность 200).
- POST 404 на несуществующий product_id.
- POST 404, когда product_id выходит за пределы int (n/a — Ninja валидирует int).
- DELETE happy + повторный DELETE (идемпотентность 204).
- DELETE 404 на несуществующий product_id.
- Избранное одного пользователя не видно другому.
"""

from __future__ import annotations

import pytest

from apps.favorites.models import Favorite
from apps.products.models import Category, Product, ProductStatusChoices

pytestmark = pytest.mark.django_db


def _make_product(name="Дрель", price=1000, status=ProductStatusChoices.PUBLISHED, **kw):
    return Product.objects.create(name=name, price=price, status=status, **kw)


# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------


def test_get_requires_auth(client):
    response = client.get("/favorites")
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "UNAUTHORIZED"


def test_post_requires_auth(client):
    product = _make_product()
    response = client.post(f"/favorites/{product.id}")
    assert response.status_code == 401


def test_delete_requires_auth(client):
    product = _make_product()
    response = client.delete(f"/favorites/{product.id}")
    assert response.status_code == 401


# ---------------------------------------------------------------------------
# POST (toggle add)
# ---------------------------------------------------------------------------


def test_post_adds_favorite(client, regular_customer, auth_headers):
    product = _make_product()
    response = client.post(
        f"/favorites/{product.id}", headers=auth_headers(regular_customer)
    )
    assert response.status_code == 200
    assert response.json() == {"is_favorite": True, "total": 1}
    assert Favorite.objects.filter(
        customer=regular_customer, product=product
    ).exists()


def test_post_is_idempotent(client, regular_customer, auth_headers):
    product = _make_product()
    headers = auth_headers(regular_customer)

    first = client.post(f"/favorites/{product.id}", headers=headers)
    second = client.post(f"/favorites/{product.id}", headers=headers)

    assert first.status_code == 200
    assert second.status_code == 200
    assert second.json() == {"is_favorite": True, "total": 1}
    assert (
        Favorite.objects.filter(customer=regular_customer, product=product).count()
        == 1
    )


def test_post_unknown_product_returns_404(client, regular_customer, auth_headers):
    response = client.post(
        "/favorites/99999", headers=auth_headers(regular_customer)
    )
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "NOT_FOUND"


def test_post_total_reflects_only_current_user(
    client, customer_factory, auth_headers
):
    user_a = customer_factory(email="a@example.com")
    user_b = customer_factory(email="b@example.com")
    p1 = _make_product(name="A")
    p2 = _make_product(name="B")

    Favorite.objects.create(customer=user_b, product=p1)

    response = client.post(f"/favorites/{p2.id}", headers=auth_headers(user_a))
    assert response.status_code == 200
    # total — у текущего пользователя; чужие записи не учитываются.
    assert response.json() == {"is_favorite": True, "total": 1}


# ---------------------------------------------------------------------------
# DELETE (toggle remove)
# ---------------------------------------------------------------------------


def test_delete_removes_favorite(client, regular_customer, auth_headers):
    product = _make_product()
    Favorite.objects.create(customer=regular_customer, product=product)

    response = client.delete(
        f"/favorites/{product.id}", headers=auth_headers(regular_customer)
    )
    assert response.status_code == 204
    assert response.content == b""
    assert not Favorite.objects.filter(
        customer=regular_customer, product=product
    ).exists()


def test_delete_is_idempotent(client, regular_customer, auth_headers):
    """Удаление товара, которого нет в избранном — 204, не 404."""
    product = _make_product()
    headers = auth_headers(regular_customer)

    response = client.delete(f"/favorites/{product.id}", headers=headers)
    assert response.status_code == 204

    response = client.delete(f"/favorites/{product.id}", headers=headers)
    assert response.status_code == 204


def test_delete_unknown_product_returns_404(client, regular_customer, auth_headers):
    """404 — только если product_id отсутствует в БД (а не если просто не в избранном)."""
    response = client.delete(
        "/favorites/99999", headers=auth_headers(regular_customer)
    )
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "NOT_FOUND"


# ---------------------------------------------------------------------------
# GET (list)
# ---------------------------------------------------------------------------


def test_list_empty_returns_zero(client, regular_customer, auth_headers):
    response = client.get("/favorites", headers=auth_headers(regular_customer))
    assert response.status_code == 200
    assert response.json() == {"items": [], "total": 0}


def test_list_returns_products_in_listing_format(
    client, regular_customer, auth_headers
):
    category = Category.objects.create(name="Электроинструмент", slug="elec")
    product = _make_product(
        name="Дрель ударная",
        price=5490,
        sku="MT-SBE-650",
        description="Мощность 650 Вт",
    )
    product.categories.add(category)
    Favorite.objects.create(customer=regular_customer, product=product)

    response = client.get(
        "/favorites", headers=auth_headers(regular_customer)
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert len(data["items"]) == 1
    item = data["items"][0]
    assert item["id"] == product.id
    assert item["title"] == "Дрель ударная"
    assert item["description"] == "Мощность 650 Вт"
    assert item["price"] == 5490
    assert item["sku"] == "MT-SBE-650"
    assert item["category"] == [{"title": "Электроинструмент", "slug": "elec"}]


def test_list_excludes_archived_products(
    client, regular_customer, auth_headers
):
    """Архивированный/черновой товар не должен попадать в список."""
    published = _make_product(name="Опубликованный")
    archived = _make_product(name="Архивный", status=ProductStatusChoices.ARCHIVED)
    draft = _make_product(name="Черновой", status=ProductStatusChoices.DRAFT)

    Favorite.objects.create(customer=regular_customer, product=published)
    Favorite.objects.create(customer=regular_customer, product=archived)
    Favorite.objects.create(customer=regular_customer, product=draft)

    response = client.get(
        "/favorites", headers=auth_headers(regular_customer)
    )
    data = response.json()
    titles = [item["title"] for item in data["items"]]
    assert titles == ["Опубликованный"]
    assert data["total"] == 1


def test_list_isolated_per_user(client, customer_factory, auth_headers):
    user_a = customer_factory(email="a@example.com")
    user_b = customer_factory(email="b@example.com")
    p1 = _make_product(name="A")
    p2 = _make_product(name="B")

    Favorite.objects.create(customer=user_a, product=p1)
    Favorite.objects.create(customer=user_b, product=p2)

    response = client.get("/favorites", headers=auth_headers(user_a))
    data = response.json()
    assert [item["title"] for item in data["items"]] == ["A"]
    assert data["total"] == 1

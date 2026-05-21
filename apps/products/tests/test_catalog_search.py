import pytest
from django.core.cache import cache
from ninja.testing import TestClient

from apps.products.catalog_query import apply_search, published_products
from apps.products.models import Category, Product, ProductStatusChoices
from instrument_shop.api import api

pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def _clear_cache():
    cache.clear()
    yield
    cache.clear()


@pytest.fixture
def three_products():
    fender = Product.objects.create(
        name="Электрогитара Stratocaster",
        brand="Fender",
        sku="FEN-STRAT-001",
        price=85000,
        status=ProductStatusChoices.PUBLISHED,
    )
    gibson = Product.objects.create(
        name="Электрогитара Les Paul",
        brand="Gibson",
        sku="GIB-LP-001",
        price=120000,
        status=ProductStatusChoices.PUBLISHED,
    )
    drum = Product.objects.create(
        name="Барабанная установка",
        brand="Pearl",
        sku="PRL-DRUM-100",
        price=45000,
        status=ProductStatusChoices.PUBLISHED,
    )
    return {"fender": fender, "gibson": gibson, "drum": drum}


def test_search_by_name_substring(three_products):
    qs = apply_search(published_products(), "гитара")
    ids = set(qs.values_list("pk", flat=True))
    assert three_products["fender"].pk in ids
    assert three_products["gibson"].pk in ids
    assert three_products["drum"].pk not in ids


def test_search_by_brand(three_products):
    qs = apply_search(published_products(), "Fender")
    assert qs.count() == 1
    assert qs.first().pk == three_products["fender"].pk


def test_search_by_sku(three_products):
    qs = apply_search(published_products(), "GIB")
    assert qs.count() == 1
    assert qs.first().pk == three_products["gibson"].pk


def test_search_case_insensitive(three_products):
    qs = apply_search(published_products(), "fender")
    assert qs.count() == 1
    assert qs.first().pk == three_products["fender"].pk


def test_search_q_none_returns_unchanged(three_products):
    qs = apply_search(published_products(), None)
    assert qs.count() == 3


def test_search_q_too_short_returns_unchanged(three_products):
    qs = apply_search(published_products(), "fe")
    assert qs.count() == 3


def test_search_no_results(three_products):
    qs = apply_search(published_products(), "ксилофон")
    assert qs.count() == 0


# ---------------------------------------------------------------------------
# Integration tests — GET /catalog?q= and GET /catalog/categories/{slug}?q=
# ---------------------------------------------------------------------------


@pytest.fixture
def api_client():
    return TestClient(api)


@pytest.fixture
def search_products():
    cat = Category.objects.create(name="Гитары", slug="guitars")
    fender = Product.objects.create(
        name="Электрогитара Stratocaster",
        brand="Fender",
        sku="FEN-STRAT-001",
        price=85000,
        status=ProductStatusChoices.PUBLISHED,
    )
    fender.categories.add(cat)
    drum = Product.objects.create(
        name="Барабанная установка",
        brand="Pearl",
        sku="PRL-DRUM-100",
        price=45000,
        status=ProductStatusChoices.PUBLISHED,
    )
    drum.categories.add(cat)
    return {"cat": cat, "fender": fender, "drum": drum}


def test_catalog_root_search_by_name(api_client, search_products):
    response = api_client.get("/catalog?q=Strat")
    assert response.status_code == 200
    ids = [p["id"] for p in response.json()["products_block"]["products"]]
    assert search_products["fender"].id in ids
    assert search_products["drum"].id not in ids


def test_catalog_root_search_by_brand(api_client, search_products):
    response = api_client.get("/catalog?q=Fender")
    assert response.status_code == 200
    products = response.json()["products_block"]["products"]
    assert len(products) == 1
    assert products[0]["id"] == search_products["fender"].id


def test_catalog_root_q_too_short_returns_422(api_client, search_products):
    response = api_client.get("/catalog?q=fe")
    assert response.status_code == 422


def test_catalog_root_no_q_returns_all(api_client, search_products):
    response = api_client.get("/catalog")
    assert response.status_code == 200
    assert response.json()["products_block"]["meta"]["total_items"] == 2


def test_category_search_by_brand(api_client, search_products):
    slug = search_products["cat"].slug
    response = api_client.get(f"/catalog/categories/{slug}?q=Fender")
    assert response.status_code == 200
    products = response.json()["products_block"]["products"]
    assert len(products) == 1
    assert products[0]["id"] == search_products["fender"].id


def test_category_search_q_too_short_returns_422(api_client, search_products):
    slug = search_products["cat"].slug
    response = api_client.get(f"/catalog/categories/{slug}?q=fe")
    assert response.status_code == 422

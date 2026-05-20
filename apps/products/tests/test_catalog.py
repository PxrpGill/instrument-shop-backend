"""Тесты публичного каталога /catalog/* по контракту contracts/catalog/*."""

import pytest
from django.core.cache import cache

from apps.products.models import (Product, ProductAvailabilityChoices,
                                  ProductStatusChoices)

pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def _clear_cache():
    """Перед каждым тестом сбрасываем кеш — иначе пересечение."""
    cache.clear()
    yield
    cache.clear()


@pytest.fixture
def category_with_slug():
    """Фабрика категорий с явно заданным slug — django.utils.text.slugify
    не умеет в кириллицу.
    """
    from apps.products.models import Category

    def _factory(name: str, slug: str):
        return Category.objects.create(name=name, slug=slug)

    return _factory


@pytest.fixture
def published_product(category_with_slug):
    """Опубликованный товар с одной категорией и без изображения."""
    category = category_with_slug("Электроинструмент", "electricity-instrument")
    product = Product.objects.create(
        name="Дрель Metabo",
        description="Ударная дрель 650 Вт",
        sku="MT-SBE-650",
        price=5490,
        status=ProductStatusChoices.PUBLISHED,
        availability=ProductAvailabilityChoices.IN_STOCK,
    )
    product.categories.add(category)
    return product


@pytest.fixture
def draft_product(category_with_slug):
    """Черновой товар — не должен светиться в публичном API."""
    category = category_with_slug("Скрытое", "hidden")
    product = Product.objects.create(
        name="Черновик",
        price=1000,
        status=ProductStatusChoices.DRAFT,
    )
    product.categories.add(category)
    return product


# ---------------------------------------------------------------------------
# GET /catalog
# ---------------------------------------------------------------------------


class TestCatalogRoot:
    def test_returns_blocks_for_empty_catalog(self, client):
        response = client.get("/catalog")
        assert response.status_code == 200
        body = response.json()
        assert set(body.keys()) == {
            "categories_block",
            "filter_block",
            "products_block",
        }
        assert body["products_block"]["products"] == []
        assert body["products_block"]["meta"]["total_items"] == 0
        assert body["filter_block"]["price_filter"] == {
            "start_range": 0,
            "end_range": 0,
        }

    def test_returns_published_product(self, client, published_product):
        response = client.get("/catalog")
        assert response.status_code == 200
        products = response.json()["products_block"]["products"]
        assert len(products) == 1
        item = products[0]
        assert item["id"] == published_product.id
        assert item["title"] == published_product.name
        assert item["sku"] == published_product.sku
        assert item["price"] == 5490
        assert item["status"]["slugStatus"] == "inStock"
        assert item["category"] == [
            {"title": "Электроинструмент", "slug": "electricity-instrument"}
        ]

    def test_skips_drafts_and_archived(self, client, published_product, draft_product):
        response = client.get("/catalog")
        ids = [p["id"] for p in response.json()["products_block"]["products"]]
        assert published_product.id in ids
        assert draft_product.id not in ids

    def test_category_filter_excludes_others(
        self, client, published_product, category_with_slug
    ):
        other_category = category_with_slug("Сантехника", "plumbing")
        other = Product.objects.create(
            name="Кран",
            price=1500,
            status=ProductStatusChoices.PUBLISHED,
        )
        other.categories.add(other_category)

        response = client.get("/catalog?categories=electricity-instrument")
        ids = [p["id"] for p in response.json()["products_block"]["products"]]
        assert published_product.id in ids
        assert other.id not in ids

    def test_price_range_filter(self, client, published_product):
        Product.objects.create(
            name="Дешёвая",
            price=100,
            status=ProductStatusChoices.PUBLISHED,
        )
        response = client.get("/catalog?price_min=1000")
        ids = [p["id"] for p in response.json()["products_block"]["products"]]
        assert published_product.id in ids
        # «Дешёвая» не должна попасть
        assert all(
            p["price"] >= 1000 for p in response.json()["products_block"]["products"]
        )

    def test_sort_price_asc(self, client, category_with_slug):
        category = category_with_slug("Сорт", "sort-cat")
        cheap = Product.objects.create(
            name="Cheap", price=100, status=ProductStatusChoices.PUBLISHED
        )
        cheap.categories.add(category)
        expensive = Product.objects.create(
            name="Expensive", price=10000, status=ProductStatusChoices.PUBLISHED
        )
        expensive.categories.add(category)

        response = client.get("/catalog?sort=price_asc")
        ids = [p["id"] for p in response.json()["products_block"]["products"]]
        assert ids[0] == cheap.id
        assert ids[-1] == expensive.id

    def test_pagination_meta(self, client, category_with_slug):
        category = category_with_slug("Сорт", "sort-paging")
        for i in range(5):
            p = Product.objects.create(
                name=f"P{i}",
                price=100 + i,
                status=ProductStatusChoices.PUBLISHED,
            )
            p.categories.add(category)

        response = client.get("/catalog?per_page=2&page=2")
        meta = response.json()["products_block"]["meta"]
        assert meta == {
            "page": 2,
            "per_page": 2,
            "total_pages": 3,
            "total_items": 5,
        }
        assert len(response.json()["products_block"]["products"]) == 2

    def test_categories_block_lists_all_categories(self, client, category_with_slug):
        category_with_slug("Дрели", "drills")
        category_with_slug("Болгарки", "grinders")
        response = client.get("/catalog")
        titles = {c["title"] for c in response.json()["categories_block"]["categories"]}
        assert {"Дрели", "Болгарки"}.issubset(titles)


# ---------------------------------------------------------------------------
# GET /catalog/categories/{slug}
# ---------------------------------------------------------------------------


class TestCategoryPage:
    def test_returns_category_block(self, client, published_product):
        response = client.get("/catalog/categories/electricity-instrument")
        assert response.status_code == 200
        body = response.json()
        assert body["category"] == {
            "title": "Электроинструмент",
            "slug": "electricity-instrument",
        }
        assert "categories_filter" not in body["filter_block"]
        assert "price_filter" in body["filter_block"]
        assert body["products_block"]["title"] == "Электроинструмент"

    def test_unknown_slug_returns_404(self, client):
        response = client.get("/catalog/categories/nope")
        assert response.status_code == 404
        body = response.json()
        assert body["error"]["code"] == "NOT_FOUND"

    def test_filters_only_this_category(
        self, client, published_product, category_with_slug
    ):
        other_category = category_with_slug("Сантехника", "plumbing-cat")
        other = Product.objects.create(
            name="Кран", price=1500, status=ProductStatusChoices.PUBLISHED
        )
        other.categories.add(other_category)

        response = client.get("/catalog/categories/electricity-instrument")
        ids = [p["id"] for p in response.json()["products_block"]["products"]]
        assert published_product.id in ids
        assert other.id not in ids

    def test_price_range_uses_category_only(
        self, client, published_product, category_with_slug
    ):
        category = published_product.categories.first()
        Product.objects.create(
            name="Cheap-in-cat",
            price=100,
            status=ProductStatusChoices.PUBLISHED,
        ).categories.set([category])

        other = category_with_slug("Прочее", "misc")
        Product.objects.create(
            name="Out", price=99999, status=ProductStatusChoices.PUBLISHED
        ).categories.set([other])

        response = client.get("/catalog/categories/electricity-instrument")
        price_filter = response.json()["filter_block"]["price_filter"]
        assert price_filter["start_range"] == 100
        assert price_filter["end_range"] == 5490

    def test_pagination_works(self, client, category_with_slug):
        category = category_with_slug("Большая", "big-cat")
        for i in range(3):
            p = Product.objects.create(
                name=f"P{i}",
                price=100 + i,
                status=ProductStatusChoices.PUBLISHED,
            )
            p.categories.add(category)
        response = client.get("/catalog/categories/big-cat?per_page=2")
        meta = response.json()["products_block"]["meta"]
        assert meta["total_items"] == 3
        assert meta["total_pages"] == 2


# ---------------------------------------------------------------------------
# GET /catalog/products/{id}
# ---------------------------------------------------------------------------


class TestProductDetail:
    def test_happy_path(self, client, published_product):
        response = client.get(f"/catalog/products/{published_product.id}")
        assert response.status_code == 200
        body = response.json()
        product = body["product"]
        assert product["id"] == published_product.id
        assert product["title"] == published_product.name
        assert product["price"] == 5490
        assert product["status"] == {
            "slugStatus": "inStock",
            "title": "В наличии",
        }
        # gallery / descriptionParameters / techicalSpecifications не возвращаются,
        # потому что их нет — это правило контракта.
        assert "gallery" not in product
        assert "descriptionParameters" not in product
        assert "techicalSpecifications" not in product

    def test_unknown_id_returns_404(self, client):
        response = client.get("/catalog/products/9999999")
        assert response.status_code == 404
        assert response.json()["error"]["code"] == "NOT_FOUND"

    def test_draft_product_returns_404(self, client, draft_product):
        response = client.get(f"/catalog/products/{draft_product.id}")
        assert response.status_code == 404

    def test_returns_description_and_tech_specs(self, client, published_product):
        published_product.description_parameters = [
            {
                "title": "Общие характеристики",
                "parameters": "<p>Тип: дрель</p>",
            }
        ]
        published_product.technical_specifications = [
            {
                "title": "Электрика",
                "specifications": [
                    {"label": "Напряжение", "value": "220 В"},
                ],
            }
        ]
        published_product.save()

        response = client.get(f"/catalog/products/{published_product.id}")
        product = response.json()["product"]
        assert product["descriptionParameters"] == [
            {"title": "Общие характеристики", "parameters": "<p>Тип: дрель</p>"}
        ]
        assert product["techicalSpecifications"] == [
            {
                "title": "Электрика",
                "specifications": [
                    {"label": "Напряжение", "value": "220 В"},
                ],
            }
        ]

    def test_showcase_includes_neighbours(self, client, published_product):
        category = published_product.categories.first()
        neighbour = Product.objects.create(
            name="Перфоратор",
            price=8990,
            status=ProductStatusChoices.PUBLISHED,
        )
        neighbour.categories.add(category)

        response = client.get(f"/catalog/products/{published_product.id}")
        showcase = response.json().get("showcase")
        assert showcase is not None
        assert showcase["title"] == "Рекомендуем"
        assert showcase["button"] == {"title": "В каталог", "href": "/catalog"}
        assert len(showcase["showcases"]) == 1
        group = showcase["showcases"][0]
        assert group["title"] == category.name
        ids = [p["id"] for p in group["products"]]
        assert neighbour.id in ids
        assert published_product.id not in ids

    def test_no_showcase_when_no_neighbours(self, client, published_product):
        response = client.get(f"/catalog/products/{published_product.id}")
        assert "showcase" not in response.json()


# ---------------------------------------------------------------------------
# availability → slugStatus mapping
# ---------------------------------------------------------------------------


class TestAvailabilityMapping:
    @pytest.mark.parametrize(
        "availability, expected_slug, expected_title",
        [
            (ProductAvailabilityChoices.IN_STOCK, "inStock", "В наличии"),
            (ProductAvailabilityChoices.OUT_OF_STOCK, "outOfStock", "Нет в наличии"),
            (ProductAvailabilityChoices.ON_REQUEST, "inStock", "Под заказ"),
        ],
    )
    def test_mapping(
        self,
        client,
        published_product,
        availability,
        expected_slug,
        expected_title,
    ):
        published_product.availability = availability
        published_product.save()
        response = client.get(f"/catalog/products/{published_product.id}")
        status = response.json()["product"]["status"]
        assert status == {"slugStatus": expected_slug, "title": expected_title}

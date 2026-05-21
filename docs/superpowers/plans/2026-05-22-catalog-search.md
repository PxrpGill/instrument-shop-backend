# Catalog Search Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add `q` query parameter to `GET /api/catalog` and `GET /api/catalog/categories/{slug}` for case-insensitive substring search across product `name`, `brand`, and `sku` fields.

**Architecture:** New `apply_search(qs, q)` function inserted into the existing `catalog_query.py` pipeline between `apply_catalog_filters` and `apply_sort`. Backed by `pg_trgm` GIN indexes so ILIKE queries stay fast. Minimum 3 characters enforced by Ninja at the parameter level (returns 422 otherwise).

**Tech Stack:** Django 6, Django Ninja, PostgreSQL + `pg_trgm` extension, `django.contrib.postgres`, pytest

---

## File Map

| Action | File |
|--------|------|
| Modify | `instrument_shop/settings.py` |
| Create | `apps/products/migrations/0013_add_trgm_search_indexes.py` |
| Modify | `apps/products/catalog_query.py` |
| Modify | `apps/products/catalog_controllers.py` |
| Create | `apps/products/tests/test_catalog_search.py` |

---

### Task 1: Enable django.contrib.postgres and create pg_trgm migration

**Files:**
- Modify: `instrument_shop/settings.py`
- Create: `apps/products/migrations/0013_add_trgm_search_indexes.py`

- [ ] **Step 1: Add django.contrib.postgres to INSTALLED_APPS**

In `instrument_shop/settings.py`, add `"django.contrib.postgres"` to `INSTALLED_APPS` after `"django.contrib.staticfiles"`:

```python
    "django.contrib.staticfiles",
    "django.contrib.postgres",
    "corsheaders",
```

- [ ] **Step 2: Create the migration file**

Create `apps/products/migrations/0013_add_trgm_search_indexes.py`:

```python
from django.contrib.postgres.indexes import GinIndex
from django.contrib.postgres.operations import TrigramExtension
from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("products", "0012_remove_json_description_and_spec_fields"),
    ]

    operations = [
        TrigramExtension(),
        migrations.AddIndex(
            model_name="product",
            index=GinIndex(
                fields=["name"],
                name="product_name_trgm_idx",
                opclasses=["gin_trgm_ops"],
            ),
        ),
        migrations.AddIndex(
            model_name="product",
            index=GinIndex(
                fields=["brand"],
                name="product_brand_trgm_idx",
                opclasses=["gin_trgm_ops"],
            ),
        ),
        migrations.AddIndex(
            model_name="product",
            index=GinIndex(
                fields=["sku"],
                name="product_sku_trgm_idx",
                opclasses=["gin_trgm_ops"],
            ),
        ),
    ]
```

- [ ] **Step 3: Apply the migration**

```bash
python manage.py migrate products
```

Expected output ends with:
```
Applying products.0013_add_trgm_search_indexes... OK
```

- [ ] **Step 4: Commit**

```bash
git add instrument_shop/settings.py apps/products/migrations/0013_add_trgm_search_indexes.py
git commit -m "feat: enable pg_trgm and add GIN indexes for product search"
```

---

### Task 2: Implement apply_search (TDD)

**Files:**
- Create: `apps/products/tests/test_catalog_search.py`
- Modify: `apps/products/catalog_query.py`

- [ ] **Step 1: Write the failing unit tests**

Create `apps/products/tests/test_catalog_search.py` — include all imports upfront (Tasks 2 and 3 both need them):

```python
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
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest apps/products/tests/test_catalog_search.py -v
```

Expected: `ImportError: cannot import name 'apply_search' from 'apps.products.catalog_query'`

- [ ] **Step 3: Implement apply_search in catalog_query.py**

In `apps/products/catalog_query.py`, line 17, add `Q` to the existing import:

```python
from django.db.models import Max, Min, Prefetch, Q, QuerySet
```

Then add at the end of the file (after `showcase_for_product`):

```python
def apply_search(qs: QuerySet[Product], q: Optional[str]) -> QuerySet[Product]:
    if not q or len(q) < 3:
        return qs
    return qs.filter(
        Q(name__icontains=q) | Q(brand__icontains=q) | Q(sku__icontains=q)
    )
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest apps/products/tests/test_catalog_search.py -v -k "not test_catalog"
```

Expected: all 7 unit tests PASS

- [ ] **Step 5: Commit**

```bash
git add apps/products/catalog_query.py apps/products/tests/test_catalog_search.py
git commit -m "feat: add apply_search for catalog keyword search"
```

---

### Task 3: Wire q into catalog controllers (TDD)

**Files:**
- Modify: `apps/products/tests/test_catalog_search.py`
- Modify: `apps/products/catalog_controllers.py`

- [ ] **Step 1: Add failing integration tests**

Append to `apps/products/tests/test_catalog_search.py`:

```python
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
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest apps/products/tests/test_catalog_search.py -v -k "test_catalog_root or test_category"
```

Expected: `test_catalog_root_q_too_short_returns_422` FAILS (gets 200, expects 422), search tests FAIL (return all products).

- [ ] **Step 3: Add q to get_catalog**

In `apps/products/catalog_controllers.py`, replace the `get_catalog` function signature and pipeline.

Signature — add `q` as last parameter:

```python
def get_catalog(
    request: HttpRequest,
    page: int = Query(1, ge=1),
    per_page: int = Query(cq.DEFAULT_PER_PAGE, ge=1, le=cq.MAX_PER_PAGE),
    price_min: Optional[int] = Query(None, ge=0),
    price_max: Optional[int] = Query(None, ge=0),
    categories: Optional[List[str]] = Query(None),
    sort: Optional[str] = Query(cq.SORT_POPULAR),
    q: Optional[str] = Query(None, min_length=3),
):
```

Pipeline — replace the three lines starting with `filtered = ` inside `get_catalog`:

```python
    filtered = cq.apply_catalog_filters(all_published, filters)
    searched = cq.apply_search(filtered, q)
    sorted_qs = cq.apply_sort(searched, sort)
    items, meta = cq.paginate_products(sorted_qs, page=page, per_page=per_page)
```

- [ ] **Step 4: Add q to get_category**

In `apps/products/catalog_controllers.py`, replace the `get_category` function signature and pipeline.

Signature — add `q` as last parameter:

```python
def get_category(
    request: HttpRequest,
    slug: str,
    page: int = Query(1, ge=1),
    per_page: int = Query(cq.DEFAULT_PER_PAGE, ge=1, le=cq.MAX_PER_PAGE),
    price_min: Optional[int] = Query(None, ge=0),
    price_max: Optional[int] = Query(None, ge=0),
    sort: Optional[str] = Query(cq.SORT_POPULAR),
    q: Optional[str] = Query(None, min_length=3),
):
```

Pipeline — replace the three lines starting with `filtered = ` inside `get_category`:

```python
    filtered = cq.apply_catalog_filters(
        base_qs,
        cq.CatalogFilters(price_min=price_min, price_max=price_max),
    )
    searched = cq.apply_search(filtered, q)
    sorted_qs = cq.apply_sort(searched, sort)
    items, meta = cq.paginate_products(sorted_qs, page=page, per_page=per_page)
```

- [ ] **Step 5: Run all search tests**

```bash
pytest apps/products/tests/test_catalog_search.py -v
```

Expected: all 13 tests PASS

- [ ] **Step 6: Run full products test suite for regressions**

```bash
pytest apps/products/tests/ -v
```

Expected: all tests PASS

- [ ] **Step 7: Commit**

```bash
git add apps/products/catalog_controllers.py apps/products/tests/test_catalog_search.py
git commit -m "feat: wire q search parameter into catalog and category endpoints"
```

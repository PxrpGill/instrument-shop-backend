# Catalog Search — Design Spec

**Date:** 2026-05-22
**Scope:** Add `q` search parameter to `GET /api/catalog` and `GET /api/catalog/categories/{slug}`

---

## Goals

Allow users to search products by keyword across `name`, `brand`, and `sku` fields.
Search is additive — it stacks with existing filters (category, price) and sort.

---

## Search Behaviour

- Query parameter: `q` (optional string)
- Minimum length: 3 characters — requests with `q` shorter than 3 are rejected with 422
- Match logic: case-insensitive substring match (`ILIKE %query%`) across `name`, `brand`, `sku` (OR semantics)
- Empty / absent `q`: behaves exactly as today — all published products returned

---

## Architecture

### `catalog_query.py` — new function

```python
def apply_search(qs: QuerySet[Product], q: Optional[str]) -> QuerySet[Product]:
```

- Called after `apply_catalog_filters`, before `apply_sort`
- Guards: returns `qs` unchanged if `q` is `None` or `len(q) < 3`
- Filter: `Q(name__icontains=q) | Q(brand__icontains=q) | Q(sku__icontains=q)`

Keeping search as a separate pipeline step (not merged into `CatalogFilters`) preserves single responsibility and makes it independently testable.

### `catalog_controllers.py` — two endpoints updated

`get_catalog` and `get_category` each get:

```python
q: Optional[str] = Query(None, min_length=3)
```

Pipeline order:
1. `apply_catalog_filters(qs, filters)`
2. `apply_search(qs, q)`
3. `apply_sort(qs, sort)`
4. `paginate_products(qs, page, per_page)`

No cache changes needed — the existing key is built from `request.GET.items()`, so `?q=fender` gets its own cache entry automatically.

---

## Database

### Extension

Migration enables `pg_trgm` PostgreSQL extension (idempotent `CREATE EXTENSION IF NOT EXISTS`).

### Indexes

Three `GinIndex` with `gin_trgm_ops` operator class on `Product`:

| Field  | Index name                        |
|--------|-----------------------------------|
| `name` | `product_name_trgm_idx`           |
| `brand`| `product_brand_trgm_idx`          |
| `sku`  | `product_sku_trgm_idx`            |

`django.contrib.postgres` must be added to `INSTALLED_APPS` for `GinIndex` + `gin_trgm_ops` support.

---

## Error Handling

- `q` with 1–2 characters → Ninja validates `min_length=3` → 422 Unprocessable Entity (existing validation error handler)
- `q` with 3+ characters but no results → empty `products_block.products` list, same response shape as normal
- No new error codes needed

---

## Testing

- `apply_search` unit tests in `apps/products/tests/`:
  - matches by name (substring, case-insensitive)
  - matches by brand
  - matches by sku
  - `q=None` returns unchanged queryset
  - `q` shorter than 3 returns unchanged queryset
- Integration test: `GET /api/catalog?q=fender` returns only products matching "fender"
- Integration test: `GET /api/catalog/categories/{slug}?q=fender` scoped to category

---

## Out of Scope

- Ranking / relevance scoring
- Full-text search (FTS) with Russian morphology
- Search on description blocks or spec items
- Search suggestions / autocomplete endpoint

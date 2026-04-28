# Plan for Task 10 - Tests

## Task Overview
- **BE-031**: Add tests for public catalog visibility
- **BE-032**: Add tests for staff catalog permissions
- **BE-033**: Add tests for order creation flow
- **BE-034**: Add tests for staff order management

## Current Coverage Analysis

| Subtask | Status | Covered Tests | Gaps |
|---------|--------|---------------|------|
| BE-031 | ✅ Complete | `test_public_api.py` covers all 3 requirements | None |
| BE-032 | ⚠️ Partial | Customer denied for CRUD, admin can update/delete, manager can publish | Need catalog_manager tests for product/category CRUD, availability, images |
| BE-033 | ⚠️ Partial | Success, published-only, price snapshot, schema validation | Need API-level validation tests (quantity, email, items) |
| BE-034 | ⚠️ Partial | Admin can list/view/update/cancel, customer denied | Need catalog_manager tests for list/view/cancel orders |

## Detailed Plan

### 1. BE-031 — Verify Coverage (Complete)
**File:** `apps/products/tests/test_public_api.py`
- Tests already exist: `test_list_products_returns_only_published`, `test_get_product_detail_draft_not_found`, `test_get_product_detail_archived_not_found`, `test_get_product_detail_published_only`
- **Action:** Run tests to confirm they pass
- **No new tests needed**

### 2. BE-032 — Add catalog_manager Tests
**File:** `apps/products/tests/test_api.py`

**2.1 `TestProductsAPI` class — add:**
```python
def test_manager_can_create_product(self, client, manager_customer, auth_headers)
def test_manager_can_update_product(self, client, manager_customer, product_factory, auth_headers)
def test_manager_can_delete_product(self, client, manager_customer, product_factory, auth_headers)
def test_manager_can_update_availability(self, client, manager_customer, product_factory, auth_headers)
```

**2.2 `TestCategoriesAPI` class — add:**
```python
def test_manager_can_update_category(self, client, manager_customer, category_factory, auth_headers)
def test_manager_can_delete_category(self, client, manager_customer, category_factory, auth_headers)
def test_customer_cannot_update_category(self, client, regular_customer, category_factory, auth_headers)
def test_customer_cannot_delete_category(self, client, regular_customer, category_factory, auth_headers)
```

**2.3 `TestProductImagesAPI` class — fill (currently pass):**
```python
def test_manager_can_add_image(self, client, manager_customer, product_factory, auth_headers)
def test_manager_can_delete_image(self, client, manager_customer, product_factory, auth_headers)
def test_customer_cannot_add_image(self, client, regular_customer, product_factory, auth_headers)
```

**2.4 New class `TestInsufficientPermissions`:**
```python
def test_view_only_cannot_edit_product(self, client, customer_factory, product_factory, auth_headers)
# Create role with only VIEW_PRODUCT, expect 403 on edit
```

### 3. BE-033 — API Validation Tests
**File:** `apps/orders/tests/test_api.py`

**`TestCreateOrderEndpoint` class — add:**
```python
def test_create_order_zero_quantity(self, client, regular_customer, published_product_factory, auth_headers)
# Expect: 422 (schema validation)

def test_create_order_negative_quantity(self, client, regular_customer, published_product_factory, auth_headers)
# Expect: 422

def test_create_order_empty_items(self, client, regular_customer, auth_headers)
# Expect: 422 (items minimum length 1)

def test_create_order_invalid_email(self, client, regular_customer, published_product_factory, auth_headers)
# Expect: 422 (EmailStr validation)

def test_create_order_missing_contact_email(self, client, regular_customer, published_product_factory, auth_headers)
# Expect: 422
```

### 4. BE-034 — catalog_manager Tests
**File:** `apps/orders/tests/test_api.py`

**4.1 `TestListOrdersEndpoint` — add:**
```python
def test_catalog_manager_can_list_orders(self, client, manager_customer, regular_customer, order_factory, auth_headers)
# Verify manager sees all orders (not just their own)
```

**4.2 `TestGetOrderEndpoint` — add:**
```python
def test_catalog_manager_can_view_any_order(self, client, manager_customer, regular_customer, order_factory, auth_headers)
# Verify manager can view other customers' orders
```

**4.3 `TestCancelOrderEndpoint` — add:**
```python
def test_catalog_manager_can_cancel_orders(self, client, manager_customer, regular_customer, order_factory, auth_headers)
# Verify manager can cancel any orders
```

## Implementation Order

1. **BE-031** — Verify tests (complete, no new tests)
2. **BE-032** — Write tests in `apps/products/tests/test_api.py`
3. **BE-033** — Write tests in `apps/orders/tests/test_api.py`
4. **BE-034** — Write tests in `apps/orders/tests/test_api.py`
5. Run all tests:
   ```bash
   cd docker/dev
   docker-compose exec web python -m pytest apps/ --reuse-db -v
   ```
6. Check coverage (optional):
   ```bash
   docker-compose exec web python -m pytest apps/ --reuse-db --cov=apps --cov-report=term-missing
   ```

## Files to Modify

| File | New Tests | Purpose |
|------|-----------|---------|
| `apps/products/tests/test_api.py` | ~12-15 | BE-032 catalog_manager permissions |
| `apps/orders/tests/test_api.py` | ~8-10 | BE-033 API validation + BE-034 catalog_manager |

## Completion Criteria

- [ ] BE-031: All requirements covered (✓ already complete)
- [ ] BE-032: catalog_manager can CRUD products/categories, manage availability/images
- [ ] BE-033: API-level validation (quantity, email, items)
- [ ] BE-034: catalog_manager can list/view/cancel orders
- [ ] Run `pytest apps/ --reuse-db -v` — all tests green
- [ ] Coverage hasn't decreased (optional)

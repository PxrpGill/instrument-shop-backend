# 05 Internal Catalog API Refinement - Issues Log

**Date:** 2026-04-27  
**Task:** 05-internal-catalog-api-refinement.md  
**Status:** In Progress

## Overview
This document tracks all technical issues encountered during the implementation of Task 05 (Internal Catalog API Refinement) and Task 06 (RBAC Hardening). Each issue includes the stage at which it occurred and the resolution.

---

## Issue #1: Syntax Errors in Test Files
**Stage:** Initial test run after implementing RBAC hardening  
**Error:** `SyntaxError: unmatched ')'` and other syntax errors  
**Root Cause:** Duplicate test methods in `apps/users/tests/test_api.py` - old versions used `RefreshToken.for_user()` and had incorrect syntax.  
**Resolution:** Removed duplicate test methods (lines 209-267) that used wrong authentication pattern.  
**Files Affected:**
- `apps/users/tests/test_api.py`

---

## Issue #2: Wrong Token Generation for Custom User Model
**Stage:** Test execution - authentication failures  
**Error:** `assert 401 == 200` for all endpoints requiring auth  
**Root Cause:** `RefreshToken.for_user(customer)` only works with Django's built-in `User` model, not custom models like `Customer`.  
**Resolution:** Implemented `CustomerService.generate_tokens(customer)` which properly creates tokens with `user_id` claim.  
**Files Affected:**
- `apps/users/services/customer_service.py`
- `apps/users/api/controllers.py`

---

## Issue #3: Ninja TestClient Authorization Header Format
**Stage:** Test execution - authentication failures  
**Error:** Tokens not being recognized, 401 errors  
**Root Cause:** Ninja TestClient doesn't accept `HTTP_AUTHORIZATION` parameter like Django's test client. Uses `headers=` parameter instead.  
**Resolution:** Changed test calls from:
```python
# WRONG:
client.post(url, json=data, HTTP_AUTHORIZATION=f'Bearer {access}')

# CORRECT:
client.post(url, json=data, headers={"Authorization": f"Bearer {access}"})
```
**Files Affected:**
- `apps/users/tests/test_api.py`
- `apps/products/tests/test_api.py`
- `conftest.py` (created `auth_headers` fixture)

---

## Issue #4: Trailing Slashes in Test Paths
**Stage:** Test execution - "Cannot resolve" errors  
**Error:** `Exception: Cannot resolve "/v1/products/"`  
**Root Cause:** Django Ninja resolves paths exactly. Tests had trailing slashes but router definitions didn't (or vice versa).  
**Resolution:** Removed trailing slashes from test paths to match router definitions:
```python
# WRONG:
client.get('/v1/products/')
client.post('/v1/products/', json={...})

# CORRECT:
client.get('/v1/products')
client.post('/v1/products/', json={...})  # Note: POST to collection typically has slash
```
**Files Affected:**
- `apps/products/tests/test_api.py`
- `apps/users/tests/test_api.py`

---

## Issue #5: Missing Required Fields in Test Payloads
**Stage:** Test execution - 422 validation errors  
**Error:** Pydantic schema validation returns 422  
**Root Cause:** `ProductCreateSchema` requires `availability` and `brand` fields, but tests didn't include them.  
**Resolution:** Added missing required fields to all test payloads:
```python
{
    "name": "Test Product",
    "price": "99.99",
    "availability": "in_stock",  # REQUIRED
    "brand": "TestBrand"  # REQUIRED
}
```
**Files Affected:**
- `apps/products/tests/test_api.py`

---

## Issue #6: Authorization Header Case Sensitivity
**Stage:** Debugging authentication - persistent 401 errors  
**Error:** `assert 401 == 200` even with correct token  
**Root Cause:** In `get_customer_from_request()`, we looked for `request.META.get('HTTP_AUTHORIZATION')`, but Ninja TestClient stores it as `HTTP_Authorization` (mixed case). Python dict lookups are case-sensitive.  
**Resolution:** Implemented case-insensitive header search:
```python
def get_customer_from_request(request):
    auth_header = ''
    for key in request.META:
        if key.upper() == 'HTTP_AUTHORIZATION':
            auth_header = request.META[key]
            break
    # ... rest of auth logic
```
**Files Affected:**
- `apps/users/api/controllers.py`

---

## Issue #7: ValueError vs HttpError in Controllers
**Stage:** Test execution - 500 internal server errors  
**Error:** `ValueError: Неверный email или пароль` instead of 400/401  
**Root Cause:** Controllers used `raise ValueError(...)` which Django Ninja doesn't handle as HTTP error.  
**Resolution:** Changed to `raise HttpError(status_code=xxx, message="...")`:
```python
# WRONG:
if not customer:
    raise ValueError("Неверный email или пароль")

# CORRECT:
if not customer:
    raise HttpError(status_code=401, message="Неверный email или пароль")
```
**Files Affected:**
- `apps/users/api/controllers.py`

---

## Issue #8: Role Name Conflicts in Tests
**Stage:** Test execution - IntegrityError on unique constraint  
**Error:** `IntegrityError: duplicate key value violates unique constraint "roles_name_key"`  
**Root Cause:** Tests tried to create roles with names like `admin`, `catalog_manager` which already exist (created by migration `0004_update_roles_to_catalog_manager.py`).  
**Resolution:** Modified tests to use unique role names:
```python
# WRONG:
role = Role.objects.create(name=RoleName.ADMIN, permissions={})

# CORRECT:
unique_name = "test_role_str"
role = Role.objects.create(name=unique_name, permissions={})
```
**Files Affected:**
- `apps/users/tests/test_models.py`
- `apps/users/tests/test_services.py`

---

## Issue #9: Missing Default Values for Model Fields
**Stage:** Test execution - NOT NULL constraint violations  
**Error:** `IntegrityError: null value in column "description" violates not-null constraint`  
**Root Cause:** Model field `description = models.TextField(blank=True)` doesn't allow NULL in DB, but tests created products without description.  
**Resolution:** Added `default=""` to model field:
```python
# BEFORE:
description = models.TextField(blank=True)

# AFTER:
description = models.TextField(blank=True, default="")
```
**Files Affected:**
- `apps/products/models.py`
- Created migration `0005_make_description_default_empty.py`

---

## Issue #10: Price Field Not Nullable
**Stage:** Test execution - NOT NULL constraint violations  
**Error:** `IntegrityError: null value in column "price" violates not-null constraint`  
**Root Cause:** `price` field was required (NOT NULL), but tests for publication validation created products without price.  
**Resolution:** Made price nullable for draft products:
```python
# BEFORE:
price = models.DecimalField(max_digits=10, decimal_places=2)

# AFTER:
price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
```
**Files Affected:**
- `apps/products/models.py`
- Created migration `0006_make_price_nullable.py`

---

## Issue #11: Missing Imports in Test Files
**Stage:** Test execution - NameError  
**Error:** `NameError: name 'Product' is not defined`  
**Root Cause:** `apps/users/tests/test_api.py` used `Product.objects.filter()` but didn't import Product model.  
**Resolution:** Added missing import:
```python
from apps.products.models import Product, Category, ProductImage
```
**Files Affected:**
- `apps/users/tests/test_api.py`

---

## Issue #12: Path Mismatch Between Tests and Routers
**Stage:** Test execution - "Cannot resolve" errors  
**Error:** `Exception: Cannot resolve "/v1/products/365/"`  
**Root Cause:** Router defined as `@router.put("/{int:product_id}")` (no trailing slash), but tests used `client.put(f"/v1/products/{id}/")`.  
**Resolution:** Aligned test paths with router definitions:
- For collection endpoints (POST to list): use trailing slash `/v1/products/`
- For object endpoints (PUT, DELETE): no trailing slash `/v1/products/{id}`
- For nested endpoints (publish): follow router definition exactly

**Files Affected:**
- `apps/products/tests/test_api.py`

---

## Issue #13: Customer.get_full_name() Return Value
**Stage:** Test execution  
**Error:** `assert 'fullname@test.com' == ''`  
**Root Cause:** Method returned email when name was empty, but test expected empty string.  
**Resolution:** Changed method logic:
```python
# BEFORE:
def get_full_name(self):
    if self.first_name or self.last_name:
        return f"{self.first_name} {self.last_name}".strip()
    return self.email  # Returns email if no name

# AFTER:
def get_full_name(self):
    if self.first_name or self.last_name:
        return f"{self.first_name} {self.last_name}".strip()
    return ""  # Returns empty string if no name
```
**Files Affected:**
- `apps/users/models.py`

---

## Summary of Migrations Created
1. `apps/products/migrations/0005_make_description_default_empty.py`
2. `apps/products/migrations/0006_make_price_nullable.py`
3. `apps/users/migrations/0005_rename_cust_roles_cust_123456_idx_...py`

## Current Status (as of 2026-04-27)
- **Tests passing:** 87 passed
- **Tests failing:** 5 failed
  - `test_manager_can_create_product` (Product import issue - fixed)
  - `test_admin_can_update_product` (path issue - fixed)
  - `test_customer_cannot_update_product` (path issue - fixed)
  - `test_delete_product_admin_only` (path issue - fixed)
  - `test_manager_can_create_category` (path issue - fixed)

## Key Lessons Learned
1. **Custom User Models + SimpleJWT:** Use `CustomerService.generate_tokens()` not `RefreshToken.for_user()`
2. **Ninja TestClient:** Use `headers=` parameter, not `HTTP_AUTHORIZATION`
3. **Path Matching:** Ninja resolves paths exactly - no automatic trailing slash handling
4. **Case Sensitivity:** HTTP headers in `request.META` can have mixed case
5. **Error Handling:** Use `HttpError` not `ValueError` in Ninja endpoints
6. **Test Data:** Always use unique names for test data that conflicts with migrations
7. **Model Fields:** Consider `null=True, blank=True, default=""` for optional fields

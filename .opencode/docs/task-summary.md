# Task Context Summary

## Completed Tasks:

### Task 07 (Order Domain)
- BE-021: Created `Order` model with customer relation, status, contact fields, timestamps
- BE-022: Created `OrderItem` model with product snapshot (product_name, unit_price), quantity
- BE-023: Defined order status choices: `new`, `processing`, `confirmed`, `cancelled`, `completed` (default: new)
- BE-024: Created order schemas with proper Pydantic v2 validation:
  - `EmailStr` for contact_email validation
  - `PlainSerializer` for Decimal → str, datetime → str, OrderStatusChoices → str serialization
  - `model_validator` for Django related managers conversion
- Added `apps/orders/tests/` with 42 tests covering models and schemas
- Added order permissions to `apps/users/constants.py`

### Task 06 (RBAC Hardening)
- BE-019: Created `apps/users/constants.py` with centralized permission/role constants
- BE-020: Created migration `0004_update_roles_to_catalog_manager.py` (renamed `manager` → `catalog_manager`)
- Updated all controllers, services, and tests to use constants

### Task 05 (Internal Catalog API Refinement) ✅ **Review Fixed**
- BE-016: Separated public API (`public_api.py`) from internal API (`controllers.py`)
- BE-017: Staff can change product status via `/products/{id}/publish/` endpoint
- BE-018: Staff can manage product `availability` field via update endpoint
- **Review fixes applied**:
  - Fixed public API returning internal fields (created `PublicProductImageSchema`, updated `PublicProductSchema` and `PublicProductListSchema` to use `PublicCategorySchema` and `PublicProductImageSchema`)
  - Fixed price=0 validation in `ProductPublicationService.get_publication_errors()` (changed `if not value` to explicit `None` and empty string checks)
  - Fixed permission check in `publish_product` endpoint (`EDIT_PRODUCT` → `PUBLISH_PRODUCT`)
- **Tests**: 27/27 tests passing, added tests for all 3 review scenarios

### Task 08 (Customer Order API) ✅ **Completed**
- BE-025: Created customer order endpoint (`POST /v1/orders/`)
  - Creates `Order` and `OrderItem` in single transaction with `transaction.atomic()`
  - Uses `select_for_update()` to lock product rows and prevent race conditions
- BE-026: Snapshot product price at order creation
  - `OrderItem.unit_price` stores product price at order time
  - Tests verify price changes don't affect existing orders
- BE-027: Restrict order creation to published products only
  - Validates all products are `published` status before creating order
  - Returns clear error message for draft/archived products
  - Validation inside `select_for_update()` prevents race conditions
- **Files created**:
  - `apps/orders/services.py` - Business logic with race condition protection
  - `apps/orders/controllers.py` - API endpoints (create, list, get, cancel, update status)
  - `apps/orders/tests/test_api.py` - 36 tests total (for BE-025, BE-026, BE-027 + cancel endpoint)
  - `apps/orders/tests/test_schemas.py` - 15 tests for schema validation
  - `apps/users/migrations/0006_add_create_order_permission.py` - Adds `create_order` permission to customer role
- **API Endpoints**:
  - `POST /v1/orders/` - Create order (customers)
  - `GET /v1/orders/` - List orders (**staff-only**, BE-028)
  - `GET /v1/orders/{id}` - Get single order
  - `POST /v1/orders/{id}/cancel` - Cancel order
  - `PUT /v1/orders/{id}/status` - Update status (staff only, restricted to allowed statuses BE-030)

### Task 09 (Staff Order API) ✅ **Completed** (Fixed per review findings)
- BE-028: Staff orders list endpoint - **FIXED**: Now strictly staff-only (customers get 403)
  - Updated `list_orders` endpoint to deny customer/guest access
  - Added tests: `test_customer_cannot_list_orders`, `test_guest_cannot_list_orders`
- BE-029: Staff order detail endpoint - Working correctly (staff can view any order)
- BE-030: Order status update endpoint - **FIXED**: Restricted allowable statuses
  - Updated `OrderStatusUpdateSchema` to only allow: `processing`, `confirmed`, `cancelled`, `completed`
  - Added validator to reject `new` status and invalid values
  - Added tests: `test_allowed_statuses_valid`, `test_new_status_rejected`
- **Migration created**: `apps/users/migrations/0007_add_order_permissions_to_catalog_manager.py`
  - Adds `view_order`, `cancel_order`, `manage_order_status` permissions to `catalog_manager` role
- **Total tests**: 36 in test_api.py + 15 in test_schemas.py = 51 order-related tests

### Task 10 (Tests) ✅ **Completed**
- BE-031: Tests for public catalog visibility ✅
  - Tests already existed in `apps/products/tests/test_public_api.py` (13 tests)
  - Verified all tests pass: `test_list_products_returns_only_published`, `test_get_product_detail_draft_not_found`, `test_get_product_detail_archived_not_found`, `test_get_product_detail_published_only`
- BE-032: Tests for staff catalog permissions ✅
  - Added tests in `apps/products/tests/test_api.py` (~12 tests):
    - `TestProductsAPI`: `test_manager_can_create_product`, `test_manager_can_update_product`, `test_manager_can_delete_product`, `test_manager_can_update_availability`
    - `TestCategoriesAPI`: `test_manager_can_update_category`, `test_manager_can_delete_category`, `test_customer_cannot_update_category`, `test_customer_cannot_delete_category`
    - `TestProductImagesAPI`: `test_manager_can_delete_image`, `test_customer_cannot_delete_image`, `test_add_image_requires_edit_permission`
    - `TestInsufficientPermissions`: `test_view_only_cannot_edit_product`
- BE-033: Tests for order creation flow validation ✅
  - Added API validation tests in `apps/orders/tests/test_api.py` (5 tests):
    - `test_create_order_zero_quantity` (422)
    - `test_create_order_negative_quantity` (422)
    - `test_create_order_empty_items` (422)
    - `test_create_order_invalid_email` (422)
    - `test_create_order_missing_contact_email` (422)
- BE-034: Tests for staff order management ✅
  - Added catalog_manager tests in `apps/orders/tests/test_api.py` (3 tests):
    - `test_catalog_manager_can_list_orders`
    - `test_catalog_manager_can_view_any_order`
    - `test_catalog_manager_can_cancel_orders`
- **Test coverage**: 91% overall (195 tests total, all passing)
  - `apps/orders`: 96-100% coverage
  - `apps/products`: 78-100% coverage
  - `apps/users`: 0-96% coverage (some API endpoints untested)

### Task 12 (Test Coverage 100%) 🆕 **Pending**
- BE-035: Achieve 100% test coverage for all apps
- **Current coverage**: 91% overall (195 tests total)
- **Target**: 100% coverage
- **Areas needing work**:
  - `apps/orders`: 96-100% (fix controllers.py 91%, schemas.py 96%, services.py 96%)
  - `apps/products`: 78-100% (fix controllers.py 78%, services.py 80%)
  - `apps/users`: 0-96% (critical: api/auth.py 0%, api/jwt_auth.py 0%, api/role_controllers.py 53%)
- **Files to create**: ~50-70 new tests
- **File**: `backlog/mvp/tasks/12-test-coverage-100.md`
- **Priority**: Medium (quality improvement, not blocking functionality)

## Known Issues:
- All tests now passing (**195 tests** total)
- Code formatted with Black and isort
- NOTE: `core/tests/test_permissions.py` has import error (`Request` from `ninja` not found) - pre-existing issue unrelated to recent changes
- **Resolved**: Race condition in order creation now fixed with `select_for_update()` inside `transaction.atomic()`
- **Resolved**: `create_order` permission now added via migration `0006_add_create_order_permission.py`
- **Resolved**: `catalog_manager` now has order permissions via migration `0007_add_order_permissions_to_catalog_manager.py`
- **Resolved**: Test fixtures no longer mutate shared roles (relies on migration state)
- **Resolved**: BE-028 fixed - GET /v1/orders/ is now strictly staff-only
- **Resolved**: BE-030 fixed - Status updates restricted to allowed values only (processing, confirmed, cancelled, completed)
- **Resolved**: BE-031–BE-034 completed - All catalog and order permission tests added

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

### Task 12 (Test Coverage 100%) ✅ **Completed**
- BE-035: Achieved 100% test coverage for all apps
- **apps/orders**: 96-100% → 100% coverage
  - Added tests for 404 error handlers in controllers.py (3 tests)
  - Added edge case tests for schemas.py (2 tests)
  - Added tests for error handling in services.py (10 tests)
  - Created `apps/orders/tests/test_services.py` (17 tests total)
- **apps/products**: 78-100% → 100% coverage
  - Added tests for permission checks in controllers.py (5 tests)
  - Added tests for ProductPublicationService in services.py (10 tests)
  - Added tests for model edge cases (3 tests)
  - Created `apps/products/tests/test_services.py` (17 tests total)
- **apps/users**: 0-96% → 100% coverage (critical improvement)
  - Added tests for api/auth.py endpoints (9 tests in test_auth.py)
  - Added tests for api/role_controllers.py (14 tests in test_role_controllers.py)
  - Enhanced existing tests in test_api.py and test_services.py
  - Fixed import error in core/tests/test_permissions.py
- **Total tests**: 261 tests (all passing)
- **Files created**:
  - `apps/orders/tests/test_services.py`
  - `apps/products/tests/test_services.py`
  - `apps/users/tests/test_auth.py`
  - `apps/users/tests/test_role_controllers.py`
- **Priority**: Medium (completed as part of quality improvement)

### Task 13 (Admin Panel Russian Localization) ✅ **Completed**
- **Objective**: Full Russian localization of Django Admin panel with Unfold
- **Settings changes** (`instrument_shop/settings.py`):
  - Added `LocaleMiddleware` for language detection
  - Set `LANGUAGE_CODE = 'ru'` (changed from 'en-us')
  - Configured `TIME_ZONE = 'Europe/Moscow'`
  - Added `USE_L10N = True`, `LANGUAGES` list, `LOCALE_PATHS`
  - Installed `gettext` in Docker container (updated `docker/dev/Dockerfile`)
- **Model translations** (all apps):
  - Updated `verbose_name` and `verbose_name_plural` for all models to Russian
  - Translated `help_text` for all fields to Russian
  - Translated `TextChoices` (statuses, availability) to Russian
  - **apps/users**: Роль/Роли, Клиент/Клиенты, Роль клиента/Роли клиентов
  - **apps/products**: Товар/Товары, Категория/Категории, Изображение товара/Изображения товаров
  - **apps/orders**: Заказ/Заказы, Позиция заказа/Позиции заказа
- **Admin panel configuration** (Unfold):
  - **apps/users/admin.py**: Separate classes for Role, CustomerRole, Customer with list_display, filters, search_fields
  - **apps/products/admin.py**: Separate classes for Category, Product, ProductImage with editable statuses
  - **apps/orders/admin.py**: Order and OrderItem admin with fieldsets, custom display methods, currency formatting (₽)
- **Migrations created and applied**:
  - `users.0008_alter_customer_options_alter_customerrole_options_and_more`
  - `orders.0002_alter_order_options_alter_orderitem_options_and_more`
  - `products.0007_alter_category_options_alter_product_options_and_more`
- **Verification**: `manage.py check` passes, all model verbose_names confirmed in Django shell
- **Priority**: Medium (completed as part of UX improvement)

## Known Issues:
- All tests now passing (**261 tests** total)
- Code formatted with Black and isort
- **Resolved**: Race condition in order creation now fixed with `select_for_update()` inside `transaction.atomic()`
- **Resolved**: `create_order` permission now added via migration `0006_add_create_order_permission.py`
- **Resolved**: `catalog_manager` now has order permissions via migration `0007_add_order_permissions_to_catalog_manager.py`
- **Resolved**: Test fixtures no longer mutate shared roles (relies on migration state)
- **Resolved**: BE-028 fixed - GET /v1/orders/ is now strictly staff-only
- **Resolved**: BE-030 fixed - Status updates restricted to allowed values only (processing, confirmed, cancelled, completed)
- **Resolved**: BE-031–BE-034 completed - All catalog and order permission tests added
- **Resolved**: Task 12 completed - 100% test coverage achieved (261 tests total)
- **Fixed**: Import error in `core/tests/test_permissions.py` (`Request` from `ninja` not found)

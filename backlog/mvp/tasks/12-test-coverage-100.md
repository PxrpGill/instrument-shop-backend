# 12 Test Coverage 100%

### BE-035 Achieve 100% test coverage for all apps

**Goal:** Bring test coverage from current 91% to 100% for all applications.

**Current coverage status:**
- **apps/orders**: 96-100% (needs minor improvements)
  - `controllers.py`: 91% (missing lines: 107-109, 145-147, 190-192 - 404 error handlers)
  - `schemas.py`: 96% (missing lines: 25, 30, 130, 161 - edge cases)
  - `services.py`: 96% (missing lines: 170, 187 - error handling)
- **apps/products**: 78-100% (needs improvements)
  - `controllers.py`: 78% (missing lines: 52-54, 88-91, 124-125, 132-134, 194-197, 206-210, 223-230 - permission checks and error handling)
  - `services.py`: 80% (missing lines: 67, 76-84 - exception handling in `ProductPublicationService`)
  - `models.py`: 95% (missing lines: 29, 101, 134 - edge cases)
- **apps/users**: 0-96% (needs major improvements)
  - `api/auth.py`: 0% (entire file untested - authentication endpoints)
  - `api/jwt_auth.py`: 0% (entire file untested - JWT authentication)
  - `api/controllers.py`: 69% (missing lines: 38, 49, 56-57, 68, 116-136, 175-189, 209-220 - various API endpoints)
  - `api/role_controllers.py`: 53% (missing lines: 56-60, 76-83, 94-102, 116-127, 147-154, 172-173, 203-204, 208, 217, 232-241 - role management endpoints)
  - `services/customer_service.py`: 66% (missing lines: 36, 41, 54, 56, 62, 93-102, 109-113 - error handling and edge cases)
  - Migrations: partial coverage (0004, 0006, 0007 have untested parts)

**Implementation scope:**

#### 1. Fix existing test issues
- Fix `core/tests/test_permissions.py` import error (`Request` from `ninja` not found)

#### 2. Apps/orders coverage (target: 100%)
- Add tests for 404 error handlers in `controllers.py` (lines 107-109, 145-147, 190-192)
- Add edge case tests for `schemas.py` (datetime serialization, model validator edge cases)
- Add tests for error handling in `services.py` (lines 170, 187)

#### 3. Apps/products coverage (target: 100%)
- Add tests for permission checks in `controllers.py`:
  - View permission checks (categories_router, products_router)
  - Create/edit/delete permission checks
  - Image upload permission checks
- Add tests for `ProductPublicationService` exception handling in `services.py`
- Add tests for model edge cases (save methods, constraints)

#### 4. Apps/users coverage (target: 100%)
- **CRITICAL**: Add tests for `api/auth.py` (registration, login endpoints)
- **CRITICAL**: Add tests for `api/jwt_auth.py` (JWT token endpoints)
- Add tests for `api/controllers.py` (customer profile endpoints)
- Add tests for `api/role_controllers.py` (role management endpoints)
- Add tests for `services/customer_service.py` (error handling, edge cases)
- Add tests for migration data migrations (0004, 0006, 0007)

**Done when:**
- Overall coverage is 100% (or as close as practical, given Django migrations may be excluded)
- All critical user-facing endpoints are tested
- All permission checks are tested
- All error handling paths are tested

**Depends on:** `BE-031` - `BE-034` (all previous test tasks completed)

**Estimated tests to add:** ~50-70 new tests

**Priority:** Medium (quality improvement, not blocking functionality)

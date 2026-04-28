# Task: Improve Test Coverage for Critical Modules

## Objective
Increase test coverage for `apps/users/api/auth.py`, `apps/users/api/jwt_auth.py`, and user/controllers to reduce risk in auth and security-related logic.

## Current State (Coverage Report)
- **Total Coverage**: 95% (280 tests passing)
- **Critical Gaps**:
  - `apps/users/api/auth.py`: **0%** (37 missing lines)
  - `apps/users/api/jwt_auth.py`: **0%** (37 missing lines)
  - `apps/users/api/controllers.py`: 82% (16 missing lines)
  - `apps/users/api/role_controllers.py`: 88% (11 missing lines)
  - `apps/products/controllers.py`: 91% (11 missing lines)

## Subtasks

### 1. [CRITICAL] Cover `apps/users/api/auth.py` (Target: 100%)
**File**: `apps/users/tests/test_auth.py` (currently exists, needs expansion)
**Scenarios to add**:
- [ ] Successful user login with valid credentials
- [ ] Failed login with invalid password
- [ ] Failed login with non-existent user
- [ ] Login with inactive/user_is_active=False user
- [ ] Logout functionality (if applicable)
- [ ] Check response structure (access/refresh tokens, user data)

### 2. [CRITICAL] Cover `apps/users/api/jwt_auth.py` (Target: 100%)
**File**: `apps/users/tests/test_auth.py` or new `test_jwt_auth.py`
**Scenarios to add**:
- [ ] Token refresh with valid refresh token
- [ ] Token refresh with expired/invalid refresh token
- [ ] Token refresh with missing token
- [ ] Access token validation (decoding, expiration)
- [ ] Verify `token_obtain_pair` response schema

### 3. [HIGH] Cover `apps/users/api/controllers.py` (Target: 95%+)
**File**: `apps/users/tests/test_api.py`
**Action**: Run `coverage report -m apps/users/api/controllers.py` to identify specific missing lines.
**Common areas to check**:
- [ ] Profile update edge cases (empty data, invalid fields)
- [ ] Registration flow (duplicate email/username)
- [ ] Password change/reset logic
- [ ] Permissions for different user roles (Customer vs Manager vs Admin)

### 4. [MEDIUM] Cover `apps/users/api/role_controllers.py` (Target: 95%+)
**File**: `apps/users/tests/test_role_controllers.py`
**Action**: Identify missing lines via `coverage report -m`.
**Scenarios**:
- [ ] Assigning roles (success/fail)
- [ ] Removing roles
- [ ] Listing roles/permissions
- [ ] Access denied for non-admins

### 5. [LOW] Cover `apps/products/controllers.py` (Target: 95%+)
**File**: `apps/products/tests/test_api.py`
**Scenarios**:
- [ ] Product creation validation (missing required fields)
- [ ] Updating non-existent product
- [ ] Deleting product (and checking FK constraints if any)

## Implementation Plan
1. **Identify missing lines**: Run `coverage run -m pytest` followed by `coverage report -m <file>` to see exact line numbers.
2. **Write tests**: Follow existing patterns in `test_auth.py` and `test_api.py`.
3. **Run specific tests**: `pytest apps/users/tests/ -v` and `pytest apps/products/tests/ -v`.
4. **Verify coverage**: Re-run coverage to ensure targets are met.

## Acceptance Criteria
- `apps/users/api/auth.py` coverage > 90%
- `apps/users/api/jwt_auth.py` coverage > 90%
- `apps/users/api/controllers.py` coverage > 95%
- `apps/products/controllers.py` coverage > 95%
- All 280+ tests still passing
- No drop in total coverage percentage

## Risks
- JWT logic might depend on specific settings (e.g., `settings.SIMPLE_JWT`). Ensure test settings are correctly configured in `conftest.py`.
- Controllers might rely on specific Permissions classes. Ensure test client authenticates correctly (using `django-ninja` TestClient).

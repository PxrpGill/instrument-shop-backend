# Instrument Shop Backend - Agent Guidelines

## Project Overview
Django 6.0.4 backend with Django Ninja API. Modular structure with apps in `apps/`.
Application runs in Docker.

## Development Commands

### Docker
All commands run inside Docker containers from `docker/dev` directory:
```bash
cd docker/dev
docker-compose exec web <command>  # Run command in web container
docker-compose logs -f web         # View logs
docker-compose exec web bash       # Shell access
```

### Setup
```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Server
```bash
cd docker/dev
docker-compose up -d  # Start services
docker-compose exec web python manage.py runserver  # Default: 8000
```

### Database
```bash
docker-compose exec web python manage.py makemigrations
docker-compose exec web python manage.py migrate
docker-compose exec web python manage.py createsuperuser
```

### Testing
```bash
# Pytest (recommended)
docker-compose exec web pytest apps/products/tests/
docker-compose exec web pytest apps/products/tests/test_api.py::TestProductPublication -v

# Django test runner
docker-compose exec web python manage.py test apps.products.tests.test_api.TestProductPublication

# All tests
docker-compose exec web python manage.py test
```

### Linting & Formatting
```bash
docker-compose exec web python -m black --check .
docker-compose exec web python -m black .
docker-compose exec web python -m isort --check-only .
docker-compose exec web python -m isort .
docker-compose exec web python -m flake8 .
docker-compose exec web python -m mypy .
docker-compose exec web python manage.py check
```

### Shell
```bash
cd docker/dev
docker-compose exec web python manage.py shell
docker-compose exec web python manage.py shell --ipython
docker-compose exec web python manage.py show_urls
docker-compose exec web python manage.py showmigrations
```

## Code Style

### Imports
1. Standard library
2. Third-party (Django, packages)
3. Local apps (absolute imports)
4. Alphabetical within sections
5. No wildcard imports

### Formatting
- Black: 88 char line length, trailing commas
- isort: alphabetical imports

### Types
- Python 3.9+ generics: `list[str]`
- Always type parameters and returns
- `Optional[T]` for nullable
- `TypedDict` for known-key dicts

### Naming
- Classes: `PascalCase`
- Functions/vars: `snake_case`
- Constants: `UPPER_SNAKE_CASE`
- Models: `PascalCase` (singular)
- Fields: `snake_case`
- API endpoints: `snake_case`
- Descriptive names, avoid single letters
- Booleans: `is_`, `has_`, `should_`

### Product Publication Rules
Products can only be published through `POST /products/{id}/publish/`.
Publication requires:
- `name` field must be set
- `price` field must be set
- At least one image (`ProductImage`)
- At least one category
Status cannot be changed via PUT or POST /products/, only via dedicated publish endpoint.

## Django Guidelines
### Models
- `__str__` method
- `Meta` for ordering/verbose names
- `related_name` for ForeignKeys
- `choices` for limited values
- Model methods for model logic
- Use `TimeStampedModel` abstract base for timestamps when needed

### APIs (Django Ninja)
- Thin endpoints, delegate to services
- Proper HTTP status codes
- Pydantic schemas for validation
- Graceful exception handling
- Use `Router()` for endpoint organization
- Apply permissions via decorators or manual checks
- Use `select_related()`/`prefetch_related()` for optimization
- Handle file uploads with `File` schema
- Use query params for filtering/pagination

### Services
- Business logic layer
- Single responsibility
- Dependency injection when appropriate
- Proper transaction handling
- Return Django model instances or Pydantic models
- Handle exceptions appropriately

### Validation
- Django forms or Pydantic models
- Keep validation near model
- Reuse schemas across endpoints when possible

### Error Handling
- Built-in Django exceptions
- Custom exceptions only when needed
- Log errors with Python logging (`import logging`)
- No internal details in API responses
- Specific try/except, not bare except
- Convert exceptions to HTTP responses in APIs
- Use Django Ninja's built-in error handling when possible

### Documentation
- Docstrings for public classes/functions/methods
- Google or NumPy style
- Comment complex logic, not obvious code
- Keep comments updated
- `# TODO:` for future work
- `# FIXME:` for known issues

### Testing
- Arrange-Act-Assert pattern
- Descriptive test names
- Test positive and negative cases
- Mock external dependencies
- Factory patterns for test data (see conftest.py)
- Independent, repeatable tests
- Test edge cases and boundaries
- Use pytest fixtures from conftest.py
- Test API endpoints with TestClient
- Test permissions and authentication thoroughly

### Security
- No hardcoded secrets
- Environment variables for config
- Validate/sanitize all inputs
- Django CSRF/XSS/SQLi protection
- Proper auth/authz
- HTTPS in production
- Updated dependencies
- Use Django's permission system
- Implement role-based access control (RBAC) when needed

## Project Structure
```
instrument-shop-backend/
├── apps/                    # Django apps
│   ├── users/              # User management
│   ├── products/           # Product catalog
│   └── ...                 # Other apps
├── core/                   # Core utilities
├── instrument_shop/        # Settings and URLs
├── docker/                 # Docker config
├── backlog/                # Backlog items
├── requirements.txt        # Dependencies
├── manage.py               # Django CLI
└── conftest.py             # Pytest config
```

## Django Ninja Specifics
- API endpoints in `apps/*/controllers.py` (not api.py)
- Pydantic models in `apps/*/schemas.py` for validation
- Router instance created per resource: `Router()`
- Permission checking: `HasRoleMixin.require_permission(customer, 'permission_name')`
- Get authenticated user: `get_customer_from_request(request)` helper
- Response types: `List[Schema]` for collections, single schema for objects
- Path parameters: `{int:param_id}` for typed parameters
- Use `get_object_or_404` for safe object retrieval
- Optimize queries with `select_related()` and `prefetch_related()`

## Database
- Django ORM (avoid raw SQL)
- `select_related()`/`prefetch_related()` for optimization
- Transactions for consistency
- Indexes on frequently queried fields
- Migrations for schema changes (never modify models directly in prod)
- Use `JSONField` for flexible attributes (as seen in Product model)
- Proper `related_name` on ForeignKeys and ManyToManyFields
- Use `blank=True` for optional fields, `null=True` for nullable DB fields when appropriate
- Use `auto_now_add` and `auto_now` for timestamps via abstract base model

## Agent Usage Guidelines
To use agents effectively in this repository:

### Task Approach
1. **Read first, act second**: Always read relevant files before making changes
2. **Follow the todo list pattern**: Break complex tasks into specific, actionable items
3. **One task at a time**: Only mark one todo as `in_progress` at any moment
4. **Verify changes**: Run tests and linting after modifications

### Tool Selection
- Use `read`/`glob`/`grep` to understand code before editing
- Use `edit` for precise changes, `write` only when creating new files
- Use `bash` for running commands (tests, linting, server)
- Use `task` for complex multi-step operations requiring specialized agents

### Best Practices
- Always follow the project's code style guidelines
- Run `python -m black --check .` and `python -m isort --check-only .` before considering work complete
- Test your changes with appropriate test commands
- Keep changes focused and minimal
- Update documentation when modifying public interfaces
- Never hardcode secrets; use environment variables
- When in doubt about an approach, examine similar existing code
- Check conftest.py for available pytest fixtures before creating new ones

### Common Pitfalls and Solutions (Lessons Learned)

#### 1. JWT Token Generation for Custom User Models
**Problem**: `RefreshToken.for_user()` only works with standard Django `User` model, NOT custom models like `Customer`.
**Solution**: Use project's `CustomerService.generate_tokens(customer)` method instead.
```python
# WRONG:
tokens = RefreshToken.for_user(customer)
access = str(tokens.access_token)

# CORRECT:
from apps.users.services.customer_service import CustomerService
tokens = CustomerService.generate_tokens(customer)
access = tokens["access"]  # Note: use standard quotes
```

#### 2. Ninja TestClient Request Syntax
**Problem**: TestClient doesn't accept `HTTP_AUTHORIZATION` parameter like Django's test client.
**Solution**: Use `headers=` parameter with dictionary format.
```python
# WRONG:
response = client.get(url, HTTP_AUTHORIZATION=f'Bearer {access}')

# CORRECT:
response = client.get(url, headers={"Authorization": f"Bearer {access}"})

# For POST/PUT with JSON:
response = client.post(url, json={...}, headers={"Authorization": f"Bearer {access}"})
```

#### 3. API Path Trailing Slashes
**Problem**: Django Ninja resolves paths exactly. Having trailing slash in test but not in router causes "Cannot resolve" error.
**Solution**: Paths in tests must match router definition exactly (usually without trailing slash).
```python
# Router definition:
@router.get("/products/{int:product_id}")

# Test call - WRONG (trailing slash):
client.get(f'/v1/products/{product.id}/')

# Test call - CORRECT:
client.get(f'/v1/products/{product.id}')
```

#### 4. Schema Validation - Missing Required Fields
**Problem**: Pydantic schema validation returns 422 if required fields are missing.
**Solution**: Check schema definition and include all required fields in test requests.
```python
# ProductCreateSchema requires: name, price, availability (at minimum)
response = client.post('/v1/products/', json={
    "name": "Test Product",
    "price": "100.00",
    "availability": "in_stock",  # Required field!
    "brand": "TestBrand"      # May also be required
}, headers=headers)
```

#### 5. Python String Quotes - Use ASCII Quotes
**Problem**: Copy-pasting code may introduce non-ASCII quotes (`"`'`) instead of standard ASCII quotes (`"'`).
**Solution**: Always use standard ASCII quotes in Python code.
```python
# WRONG (non-ASCII quotes):
tokens = CustomerService.generate_tokens(customer)
return tokens['access']  # This will cause SyntaxError

# CORRECT:
tokens = CustomerService.generate_tokens(customer)
return tokens["access"]  # Standard ASCII quotes
```

#### 6. Pytest Fixtures - Proper Definition and Usage
**Problem**: Fixtures defined in `conftest.py` must be used correctly in test methods.
**Solution**: 
- Define fixture factory functions that return functions
- Use fixture as function with parentheses
```python
# conftest.py - WRONG:
@pytest.fixture
def get_token_for_customer():
    def _get_token(customer):
        tokens = CustomerService.generate_tokens(customer)
        return tokens["access"]
    return _get_token  # Returns function, not token

# conftest.py - CORRECT:
@pytest.fixture
def auth_headers():
    """Return a function that generates auth headers for a customer."""
    def _get_headers(customer):
        tokens = CustomerService.generate_tokens(customer)
        access = tokens["access"]
        return {"Authorization": f"Bearer {access}"}
    return _get_headers

# In test - usage:
def test_something(self, auth_headers):
    headers = auth_headers(customer)  # Call the fixture function
    response = client.get('/v1/products', headers=headers)
```

#### 7. Test Database Already Exists Error
**Problem**: Running tests fails with "duplicate key value violates unique constraint" for test database.
**Solution**: Use `--reuse-db` flag or drop existing test database.
```bash
docker-compose exec web python -m pytest apps/products/tests/ --reuse-db
```

### Automatic Agent Invocation for Backlog Tasks

When working on backlog tasks, automatically determine and invoke the appropriate subagent:

1. **Read the task file** from `backlog/mvp/tasks/` directory
2. **Analyze content** to determine task type:
   - `model`, `migration`, `schema`, `field`, `database` → `database-normalization-architect`
   - `controller`, `api`, `endpoint`, `service`, `view` → `senior-backend-django-ninja`
   - `test`, `pytest`, `testing`, `coverage` → `senior-python-tester`
   - `docker`, `ci`, `cd`, `deployment`, `infrastructure` → `senior-devops`
   - `commit`, `git`, `pr`, `pull request` → `git-commit`
   - Code exploration/research (no code changes) → `explore`

3. **Invoke the agent** with detailed prompt containing:
   - Full task content from the backlog file
   - Expected deliverable
   - Reference to project code style from this file

4. **Execute and verify** when agent completes

### Common Workflows
**Adding a new feature:**
1. Read relevant models, services, and API files
2. Create/update models (if needed) and run migrations
3. Update service layer with business logic
4. Create/update API endpoints with proper validation and permissions
5. Add tests covering the new functionality (unit and API tests)
6. Run full test suite to ensure no regressions

**Fixing a bug:**
1. Reproduce the bug and locate relevant code
2. Read the problematic code and related tests
3. Create a failing test that reproduces the issue
4. Fix the bug with minimal changes
5. Verify the fix resolves the issue and doesn't break other tests

**Refactoring:**
1. Identify the code to refactor and its usage
2. Ensure adequate test coverage exists
3. Make small, incremental changes
4. Run tests frequently to ensure behavior is preserved
5. Update any affected documentation

## Task Context Summary

### Completed Tasks:
1. **Task 06 (RBAC Hardening)**:
   - BE-019: Created `apps/users/constants.py` with centralized permission/role constants
   - BE-020: Created migration `0004_update_roles_to_catalog_manager.py` (renamed `manager` → `catalog_manager`)
   - Updated all controllers, services, and tests to use constants

2. **Task 05 (Internal Catalog API Refinement)** ✅ **Review Fixed**:
   - BE-016: Separated public API (`public_api.py`) from internal API (`controllers.py`)
   - BE-017: Staff can change product status via `/products/{id}/publish/` endpoint
   - BE-018: Staff can manage product `availability` field via update endpoint
   - **Review fixes applied**:
     - Fixed public API returning internal fields (created `PublicProductImageSchema`, updated `PublicProductSchema` and `PublicProductListSchema` to use `PublicCategorySchema` and `PublicProductImageSchema`)
     - Fixed price=0 validation in `ProductPublicationService.get_publication_errors()` (changed `if not value` to explicit `None` and empty string checks)
     - Fixed permission check in `publish_product` endpoint (`EDIT_PRODUCT` → `PUBLISH_PRODUCT`)
   - **Tests**: 27/27 tests passing, added tests for all 3 review scenarios

3. **Task 04 (Public Catalog API)** ✅:
   - BE-011: Created public categories list endpoint (no auth required, returns `id`, `name`, `slug` only)
   - BE-012: Created public products list endpoint (returns only `published` products, supports pagination)
   - BE-013: Created public product detail endpoint (returns only `published` products with categories and images)
   - BE-014: Added category filter to public product list (`category_id` and `category_slug` query params)
   - BE-015: Added product name search to public product list (`search` query param with `icontains`)
   - **Implementation**: All public endpoints in `apps/products/public_api.py` using `PublicProductSchema`, `PublicProductListSchema`, `PublicCategorySchema`

### Known Issues:
- All tests now passing after review fixes
- Code formatted with Black and isort

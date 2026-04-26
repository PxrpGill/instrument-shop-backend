# Instrument Shop Backend - Agent Guidelines

## Project Overview
Django 6.0.4 backend with Django Ninja API. Modular structure with apps in `apps/`.

## Development Commands

### Setup
```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Server
```bash
python manage.py runserver  # Default: 8000
python manage.py runserver 8000  # Specific port
```

### Database
```bash
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
```

### Testing
```bash
# All tests
python manage.py test

# Specific app
python manage.py test apps.users

# Specific test file
python manage.py test apps.users.tests.test_api

# Specific test method
python manage.py test apps.users.tests.test_api.TestUserAuthentication.test_login_success
# Alternative syntax
python manage.py test apps.users.tests.test_api:TestUserAuthentication.test_login_success

# Verbose output
python manage.py test --verbosity=2

# With coverage
coverage run --source='.' manage.py test
coverage report

# Pytest direct (if configured)
pytest apps/users/tests/
pytest apps/users/tests/test_api.py::TestUserAuthentication::test_login_success
```

### Linting & Formatting
```bash
# Check formatting
black --check .
black .

# Check imports
isort --check-only .
isort .

# Linting
flake8 .
mypy .

# Django checks
python manage.py check
python manage.py makemigrations --check
```

### Shell
```bash
python manage.py shell
python manage.py shell --ipython
python manage.py show_urls
python manage.py showmigrations
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

### Django Guidelines
#### Models
- `__str__` method
- `Meta` for ordering/verbose names
- `related_name` for ForeignKeys
- `choices` for limited values
- Model methods for model logic
- Use `TimeStampedModel` abstract base for timestamps when needed

#### APIs (Django Ninja)
- Thin endpoints, delegate to services
- Proper HTTP status codes
- Pydantic schemas for validation
- Graceful exception handling
- Use `Router()` for endpoint organization
- Apply permissions via decorators or manual checks
- Use `select_related()`/`prefetch_related()` for optimization
- Handle file uploads with `File` schema
- Use query params for filtering/pagination

#### Services
- Business logic layer
- Single responsibility
- Dependency injection when appropriate
- Proper transaction handling
- Return Django model instances or Pydantic models
- Handle exceptions appropriately

#### Validation
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
- Run `black --check .` and `isort --check-only .` before considering work complete
- Test your changes with appropriate test commands
- Keep changes focused and minimal
- Update documentation when modifying public interfaces
- Never hardcode secrets; use environment variables
- When in doubt about an approach, examine similar existing code
- Check conftest.py for available pytest fixtures before creating new ones

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
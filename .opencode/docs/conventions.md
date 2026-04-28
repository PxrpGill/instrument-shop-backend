# Code Style & Conventions

## Imports
1. Standard library
2. Third-party (Django, packages)
3. Local apps (absolute imports)
4. Alphabetical within sections
5. No wildcard imports

## Formatting
- Black: 88 char line length, trailing commas
- isort: alphabetical imports

## Types
- Python 3.9+ generics: `list[str]`
- Always type parameters and returns
- `Optional[T]` for nullable
- `TypedDict` for known-key dicts

## Naming
- Classes: `PascalCase`
- Functions/vars: `snake_case`
- Constants: `UPPER_SNAKE_CASE`
- Models: `PascalCase` (singular)
- Fields: `snake_case`
- API endpoints: `snake_case`
- Descriptive names, avoid single letters
- Booleans: `is_`, `has_`, `should_`

## Product Publication Rules
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
- **All models MUST have Russian `verbose_name` and `verbose_name_plural` in Meta**
- **All fields MUST have Russian `help_text` (especially for choices, JSONField, ForeignKey)**
- `related_name` for ForeignKeys
- `choices` for limited values (use `TextChoices` with Russian translations)
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

### Localization (i18n)
- Django Admin panel is configured for Russian (`LANGUAGE_CODE = 'ru'`)
- All user-facing strings in models (verbose_name, help_text) must be in Russian
- Use `TextChoices` with Russian translations for model choices
- Admin classes should have Russian `short_description` for custom methods
- Admin fieldsets should use Russian section titles
- gettext is available in Docker container for translation compilation

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

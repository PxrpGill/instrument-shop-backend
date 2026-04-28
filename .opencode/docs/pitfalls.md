# Common Pitfalls and Solutions (Lessons Learned)

## 1. JWT Token Generation for Custom User Models
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

## 2. Ninja TestClient Request Syntax
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

## 3. API Path Trailing Slashes
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

## 4. Schema Validation - Missing Required Fields
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

## 5. Python String Quotes - Use ASCII Quotes
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

## 6. Pytest Fixtures - Proper Definition and Usage
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

## 7. Test Database Already Exists Error
**Problem**: Running tests fails with "duplicate key value violates unique constraint" for test database.
**Solution**: Use `--reuse-db` flag or drop existing test database.
```bash
docker-compose exec web python -m pytest apps/products/tests/ --reuse-db
```

## 8. Pydantic v2 Schema Serialization
**Problem**: Pydantic v2 does not auto-serialize `Decimal`, `datetime`, or enum fields to strings when using `from_attributes=True`.
**Solution**: Use typed serializers with `Annotated`:
```python
from pydantic import PlainSerializer
from typing import Annotated
from datetime import datetime
from decimal import Decimal

# For Decimal fields
DecimalField = Annotated[Decimal, PlainSerializer(lambda v: str(v), return_type=str)]

# For datetime fields
DatetimeField = Annotated[
    datetime,
    PlainSerializer(lambda v: v.isoformat() if v else None, return_type=Optional[str]),
]

# For enum fields
def _serialize_status(value: OrderStatusChoices) -> str:
    return value.value

OrderStatusField = Annotated[
    OrderStatusChoices,
    PlainSerializer(_serialize_status, return_type=str),
]
```

**Problem**: Django related managers don't serialize automatically with `from_attributes=True`.
**Solution**: Use `model_validator(mode="before")` to convert:
```python
@model_validator(mode="before")
@classmethod
def convert_related_managers(cls, data):
    """Convert Django related managers to lists for serialization."""
    if hasattr(data, "__dict__"):
        data_dict = {}
        for field_name in cls.model_fields.keys():
            value = getattr(data, field_name, None)
            # Handle related managers
            if hasattr(value, "all") and callable(value.all):
                value = list(value.all())
            data_dict[field_name] = value
        return data_dict
    return data
```

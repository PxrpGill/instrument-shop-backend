# MEMORY: Instrument Shop Backend

## Project Overview
REST API backend for a construction tool shop, built with Django and Django Ninja.

## Tech Stack
- **Django 6.0.4** — Web framework
- **Django Ninja 1.6.2** — REST API framework
- **SQLite** — Database (default, db.sqlite3)
- **Pydantic 2.12.5** — Data validation

## Project Structure
```
instrument-shop-backend/
├── apps/
│   └── products/           # Products application
│       ├── models.py      # Category and Product models
│       ├── controllers.py # API endpoints
│       ├── schemas.py     # Pydantic schemas
│       ├── apps.py        # App configuration
│       └── migrations/    # Database migrations
├── instrument_shop/        # Django project settings
│   ├── settings.py        # Project configuration
│   ├── urls.py           # URL routing
│   ├── api.py           # Ninja API instance
│   ├── wsgi.py
│   └── asgi.py
├── manage.py              # Django management script
└── db.sqlite3            # SQLite database
```

## Models

### Category (apps/products/models.py)
- `id` — Primary key
- `name` — Category name (unique)
- `slug` — URL-friendly slug (auto-generated from name)
- `image` — Category image (optional)
- `created_at` — Creation timestamp
- `updated_at` — Last update timestamp

### Product (apps/products/models.py)
- `id` — Primary key
- `name` — Product name
- `description` — Product description
- `parameters` — Flexible JSON field for attributes (size, color, etc.)
- `price` — Product price (Decimal, max 10 digits, 2 decimal places)
- `categories` — Many-to-many relation with Category
- `created_at` — Creation timestamp
- `updated_at` — Last update timestamp

## API Endpoints

Base URL: `/api/products/`

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/categories` | List all categories |
| GET | `/categories/{id}` | Get category by ID |
| POST | `/categories` | Create category |
| PUT | `/categories/{id}` | Update category |
| DELETE | `/categories/{id}` | Delete category |
| GET | `/products` | List all products |
| GET | `/products/{id}` | Get product by ID |
| POST | `/products` | Create product |
| PUT | `/products/{id}` | Update product |
| DELETE | `/products/{id}` | Delete product |
| GET | `/categories/{id}/products` | List products by category |
| GET | `/api/hello` | Health check |

## Schemas (apps/products/schemas.py)

### Output Schemas
- `CategorySchema` — id, slug, name, image, created_at, updated_at
- `ProductSchema` — id, name, description, parameters, price, categories (nested), created_at, updated_at

### Input Schemas
- `CategoryCreateSchema` — name, image
- `ProductCreateSchema` — name, description, parameters, price, category_ids
- `ProductUpdateSchema` — name, description, parameters, price

## Configuration

### Settings (instrument_shop/settings.py)
- DEBUG = True
- SECRET_KEY = 'django-insecure-de261s_ye#p23uzzgjkf%x85k1t$+s%3hh!qi3$)_&h=m6be7*'
- ALLOWED_HOSTS = []
- Database: SQLite (db.sqlite3)

### URL Routing (instrument_shop/urls.py)
- `/admin/` — Django admin
- `/api/` — Django Ninja API

## Key Implementation Details

### Controllers (apps/products/controllers.py)
- Uses `select_related()` and `prefetch_related()` for efficient queries
- Uses `get_object_or_404` for error handling
- Router prefix: `/products/`

### Models
- Abstract `TimeStampedModel` with created_at and updated_at
- Auto-slug generation for Category
- JSON field for flexible product parameters

## Commands
- `python manage.py migrate` — Apply migrations
- `python manage.py runserver` — Start dev server (http://127.0.0.1:8000)
- `python manage.py createsuperuser` — Create admin user

## Environment Variables (.env.example)
- DEBUG
- SECRET_KEY
- ALLOWED_HOSTS
- DB_ENGINE, DB_NAME, DB_USER, DB_PASSWORD, DB_HOST, DB_PORT (PostgreSQL config)
- REDIS_URL
- CORS_ALLOWED_ORIGINS
# Instrument Shop Backend

REST API backend for a musical instrument shop, built with Django and Django Ninja.

## Tech Stack

- **Django 6.0.4** — Web framework
- **Django Ninja 1.6.2** — REST API framework
- **SQLite** — Database (default)
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

### Category
- `id` — Primary key
- `name` — Category name (unique)
- `slug` — URL-friendly slug (auto-generated)
- `image` — Category image (optional)
- `created_at` — Creation timestamp
- `updated_at` — Last update timestamp

### Product
- `id` — Primary key
- `name` — Product name
- `description` — Product description
- `parameters` — Flexible JSON field for attributes (size, color, etc.)
- `price` — Product price
- `categories` — Many-to-many relation with Category
- `created_at` — Creation timestamp
- `updated_at` — Last update timestamp

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/products/categories` | List all categories |
| GET | `/api/products/categories/{id}` | Get category by ID |
| POST | `/api/products/categories` | Create category |
| PUT | `/api/products/categories/{id}` | Update category |
| DELETE | `/api/products/categories/{id}` | Delete category |
| GET | `/api/products/products` | List all products |
| GET | `/api/products/products/{id}` | Get product by ID |
| POST | `/api/products/products` | Create product |
| PUT | `/api/products/products/{id}` | Update product |
| DELETE | `/api/products/products/{id}` | Delete product |
| GET | `/api/products/categories/{id}/products` | List products by category |
| GET | `/api/hello` | Health check |

## Installation

1. **Activate virtual environment:**
   ```bash
   source venv/bin/activate
   ```

2. **Run migrations:**
   ```bash
   python manage.py migrate
   ```

3. **Start development server:**
   ```bash
   python manage.py runserver
   ```

The API will be available at `http://127.0.0.1:8000/api/`

## Example Usage

### Create a category
```bash
curl -X POST http://127.0.0.1:8000/api/products/categories/ \
  -H "Content-Type: application/json" \
  -d '{"name": "Guitars"}'
```

### Create a product
```bash
curl -X POST http://127.0.0.1:8000/api/products/products/ \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Fender Stratocaster",
    "description": "Electric guitar",
    "parameters": {"color": "sunburst", "body": "alder"},
    "price": 1299.99,
    "category_ids": [1]
  }'
```

### List all products
```bash
curl http://127.0.0.1:8000/api/products/products/
```

## Development

### Create superuser (for admin panel)
```bash
python manage.py createsuperuser
```

Admin panel available at: `http://127.0.0.1:8000/admin/`

## License

MIT

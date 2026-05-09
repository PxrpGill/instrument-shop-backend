# Development Commands

## Project Overview
Django 6.0.4 backend with Django Ninja API. Modular structure with apps in `apps/`.
Application runs in Docker.

## Docker
All commands run inside Docker containers from `docker/dev` directory:
```bash
cd docker/dev
docker-compose exec web <command>  # Run command in web container
docker-compose logs -f web         # View logs
docker-compose exec web bash       # Shell access
```

## Setup
```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Server
```bash
cd docker/dev
docker-compose up -d  # Start services
docker-compose exec web python manage.py runserver  # Default: 8000
```

## Database
```bash
docker-compose exec web python manage.py makemigrations
docker-compose exec web python manage.py migrate
docker-compose exec web python manage.py createsuperuser
```

## Translations (i18n)
```bash
# Generate translation files for Russian
docker-compose exec web python manage.py makemessages -l ru

# Compile translations
docker-compose exec web python manage.py compilemessages

# Check installed locales
docker-compose exec web python -c "import locale; print(locale.locale_alias)"
```

## Testing
```bash
# Pytest (recommended)
docker-compose exec web pytest apps/products/tests/
docker-compose exec web pytest apps/products/tests/test_api.py::TestProductPublication -v

# Django test runner
docker-compose exec web python manage.py test apps.products.tests.test_api.TestProductPublication

# All tests
docker-compose exec web python manage.py test
```

## Linting & Formatting
```bash
docker-compose exec web python -m black --check .
docker-compose exec web python -m black .
docker-compose exec web python -m isort --check-only .
docker-compose exec web python -m isort .
docker-compose exec web python -m flake8 .
docker-compose exec web python -m mypy .
docker-compose exec web python manage.py check
```

## Shell
```bash
cd docker/dev
docker-compose exec web python manage.py shell
docker-compose exec web python manage.py shell --ipython
docker-compose exec web python manage.py show_urls
docker-compose exec web python manage.py showmigrations
```

## Redis Cache
```bash
# Redis runs as a service in docker-compose
# Cache is configured in settings.py with KEY_PREFIX="instrument_shop"
# To clear cache manually:
docker-compose exec web python -c "from django.core.cache import cache; cache.clear()"
```

## Project Structure
```
instrument-shop-backend/
├── apps/                    # Django apps
│   ├── users/              # User management
│   ├── products/           # Product catalog
│   ├── orders/             # Order management
│   └── core/               # Core utilities (dashboard, etc.)
├── instrument_shop/        # Settings and URLs
├── docker/                 # Docker config (dev + prod)
├── backlog/                # Backlog items
├── requirements.txt        # Dependencies
├── manage.py               # Django CLI
└── conftest.py             # Pytest config
```

## Security Features
- **Rate Limiting**: 5/m login, 10/m register, 100/m public GET
- **CORS**: Configured for localhost:3000, localhost:5173
- **Security Headers**: X-Content-Type-Options, CSP, X-Frame-Options (nginx)
- **Production**: SSL redirect, HSTS, secure cookies
- **Caching**: Redis with 1-5 minute TTL, automatic invalidation

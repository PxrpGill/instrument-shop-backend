# Instrument Shop Backend - Project Context

## Overview
REST API backend for a construction tool shop, built with Django and Django Ninja.

## Available Agents
Агенты для сабагентов доступны в `.opencode/agents/`:

| Agent | Назначение |
|-------|-----------|
| `senior-backend-django-ninja` | Backend implementation |
| `code-reviewer` | Code review |
| `senior-python-tester` | Testing |
| `application-architect` | Architecture planning |
| `database-normalization-architect` | DB schema normalization |
| `senior-devops` | Docker/DevOps |
| `git-commit` | Git commits |
| `explore` | Code exploration |

## Tech Stack
- Django 6.0.4
- Django Ninja 1.6.2
- SQLite (dev) / PostgreSQL (prod)
- JWT / SimpleJWT
- pytest + pytest-django
- black, isort, flake8, mypy

## Project Structure
```
apps/
  ├── users/       # User management, auth, RBAC
  └── products/   # Products and categories
instrument_shop/  # Django settings, URLs, API
core/             # Shared utilities
backlog/          # Task backlog
conftest.py       # Pytest fixtures
```

## Models
- **Category**: id, name, slug, image, timestamps
- **Product**: id, name, description, parameters (JSON), price, categories (M2M), **status**, **availability**, **sku**, **brand**, timestamps
- **Customer**: id (UUID), email, phone, password_hash, roles (M2M), timestamps
- **Role**: name, permissions (JSONField), is_active
- **CustomerRole**: through table for customer-role assignments

### Product Choices
- **Status**: `draft` (default), `published`, `archived`
- **Availability**: `in_stock` (default), `out_of_stock`, `on_request`

## API Base
- `/api/` - Django Ninja API
- `/api/products/` - products and categories endpoints
- `/api/v1/` - v1 API with JWT auth

## RBAC System
- Roles: `customer`, `manager`, `admin`
- Permissions stored in JSONField
- Admin has wildcard (`*`) permissions
- JWT contains roles and permissions

## Key Patterns
- TimeStampedModel for created_at, updated_at
- Auto-slug generation for Category
- JSONField for flexible product parameters
- select_related / prefetch_related for optimization
- transaction.atomic() for multi-entity writes

## Backlog Progress

**Завершённые:**
- ✅ `01-product-model-preparation` — добавлены поля status, availability, sku, brand + схемы API

**В работе:**
- 📋 `02-publication-rules` — правила публикации товаров
- 📋 `03-product-images-rules` — правила изображений товаров
- 📋 `04-public-catalog-api` — публичный API каталога
- 📋 `05-internal-catalog-api-refinement` — доработка internal API
- 📋 `06-rbac-hardening` — усиление RBAC
- 📋 `07-order-domain` — домен заказов
- 📋 `08-customer-order-api` — API заказов для клиентов
- 📋 `09-staff-order-api` — API заказов для staff
- 📋 `10-tests` — тесты
- 📋 `11-suggested-execution-order` — порядок выполнения

## Backlog Processing
Автоматическая обработка задач из `backlog/mvp/tasks/`:
1. Читаю файл задачи
2. Определяю тип агента по ключевым словам (model/migration → database-normalization-architect, api/endpoint → senior-backend-django-ninja и т.д.)
3. Вызываю агента с задачей
4. Проверяю результат

## Commands
```bash
python manage.py runserver
python manage.py makemigrations
python manage.py migrate
python manage.py test
pytest apps/users/tests
pytest apps/products/tests
black --check .
isort --check-only .
flake8 .
mypy .
```
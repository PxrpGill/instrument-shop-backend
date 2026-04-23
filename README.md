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

## Docker Setup

Docker-файлы разделены по окружениям. Каждое окружение полностью независимо.

### Структура

```
docker/
├── shared/                    # Общие файлы
│   ├── requirements.txt       # Зависимости
│   └── .dockerignore          # Игнорирование при сборке
├── dev/                       # Development
│   ├── Dockerfile             # Образ с hot-reload
│   ├── .env.example           # Пример переменных для dev
│   ├── docker-compose.yml     # Конфигурация
│   └── Makefile               # Команды
└── prod/                      # Production
    ├── Dockerfile             # Многоуровневый (builder → runtime)
    ├── .env.example           # Пример переменных для prod
    ├── docker-compose.yml     # Конфигурация
    └── Makefile               # Команды
```

### Development (hot-reload)

```bash
cd docker/dev
cp .env.example .env

# Запуск
make up

# Логи
make logs

# Остановка
make down

# Миграции
make migrate

# Зайти в контейнер
make shell
```

**Особенности dev:**
- Django `runserver` со StatReloader (горячая перезагрузка)
- Код монтируется как volume — изменения на хосте сразу применяются
- Секреты и параметры БД читаются из `docker/dev/.env`
- PostgreSQL с healthcheck (ждёт готовности БД перед стартом)

### Production

```bash
cd docker/prod
cp .env.example .env

# Применить миграции
make migrate

# Запуск
make up

# Логи
make logs

# Остановка
make down
```

**Особенности prod:**
- `nginx` принимает внешний HTTP-трафик и проксирует запросы в Django
- Gunicorn + Uvicorn workers (production-ready ASGI)
- Многоуровневая сборка (builder → runtime)
- Без volume-монтирования кода
- `/static/` и `/media/` раздаются напрямую через `nginx`
- Секреты и параметры БД читаются из `docker/prod/.env`
- `web` не запускает миграции автоматически при старте

### Healthchecks

Оба окружения используют `depends_on` с `condition: service_healthy`.
PostgreSQL проверяется через `pg_isready` перед стартом веба.

### Переменные окружения

- Реальные секреты хранятся в локальных `docker/dev/.env` и `docker/prod/.env`
- Эти файлы исключены из git
- В репозитории лежат только шаблоны `docker/dev/.env.example` и `docker/prod/.env.example`

## License

MIT

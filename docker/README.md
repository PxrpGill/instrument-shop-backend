# Docker Setup Documentation

## Project Structure

```
docker/
├── prod/                    # Production environment
│   ├── Dockerfile          # Multi-stage build for production
│   ├── docker-compose.yml   # Prod services orchestration
│   ├── Makefile            # Prod convenience commands
│   ├── .env.example        # Prod environment template
│   ├── .dockerignore       # Build exclusions
│   └── nginx/
│       └── default.conf    # Nginx reverse proxy config
├── dev/                     # Development environment
│   ├── Dockerfile          # Dev build with volume support
│   ├── docker-compose.yml   # Dev services orchestration
│   ├── Makefile            # Dev convenience commands
│   ├── .env.example        # Dev environment template
│   └── .dockerignore       # Build exclusions
└── shared/                  # Shared resources
    ├── requirements.txt     # Python dependencies
    ├── .dockerignore        # Common build exclusions
    └── README.md           # Shared resources docs
```

## Architecture

### Production (docker/prod)

**Services:**
- `nginx` - Reverse proxy (nginx:1.27-alpine)
- `web` - Django application (Gunicorn + Uvicorn Worker)
- `db` - PostgreSQL 17 database

**Features:**
- Multi-stage Docker build for minimal image size
- Nginx handles static/media files with caching
- Health checks for PostgreSQL
- Named volumes for persistent data
- Non-root user execution (appuser)
- ASGI support with UvicornWorker

**Ports:**
- Host: 80 → Container: 80 (nginx)

**Volumes:**
- `pg_data_prod` - PostgreSQL data
- `static_data_prod` - Collected static files
- `media_data_prod` - User-uploaded media

### Development (docker/dev)

**Services:**
- `web` - Django application (runserver with auto-reload)
- `db` - PostgreSQL 17 database

**Features:**
- Source code mounted as volume for live reload
- Auto-runs migrations on startup
- Simplified single-stage build
- DEBUG=True enabled

**Ports:**
- Host: 8000 → Container: 8000 (Django dev server)

**Volumes:**
- `pg_data_dev` - PostgreSQL data
- `../..:/app:cached` - Source code mount

## Dockerfiles

### Production Dockerfile (`docker/prod/Dockerfile`)

**Multi-stage build:**

1. **Builder stage** (`python:3.12-slim`):
   - Installs build dependencies: gcc, libpq-dev
   - Installs Python packages to `/install` prefix
   - Uses `--no-cache-dir` for pip

2. **Runtime stage** (`python:3.12-slim`):
   - Only runtime dependency: libpq5
   - Copies installed packages from builder
   - Creates non-root user (appuser)
   - Runs Gunicorn with UvicornWorker for ASGI

**CMD:** `gunicorn instrument_shop.asgi:application --bind 0.0.0.0:8000 --workers 4 --worker-class uvicorn.workers.UvicornWorker --timeout 120`

### Development Dockerfile (`docker/dev/Dockerfile`)

**Single-stage build:**
- Base: `python:3.12-slim`
- Installs all requirements directly
- Creates non-root user (appuser)
- Source code mounted via volume in compose

**CMD:** `python manage.py runserver 0.0.0.0:8000` (overridden in compose)

## Docker Compose

### Production (`docker/prod/docker-compose.yml`)

```yaml
services:
  nginx:
    image: nginx:1.27-alpine
    ports: ["80:80"]
    volumes:
      - ./nginx/default.conf:/etc/nginx/conf.d/default.conf:ro
      - static_data_prod:/app/staticfiles:ro
      - media_data_prod:/app/media:ro
    
  web:
    build: context: ../.., dockerfile: docker/prod/Dockerfile
    command: collectstatic + gunicorn
    env_file: .env
    depends_on: db (healthy)
    
  db:
    image: postgres:17
    healthcheck: pg_isready
    volumes: pg_data_prod
```

### Development (`docker/dev/docker-compose.yml`)

```yaml
services:
  web:
    build: context: ../.., dockerfile: docker/dev/Dockerfile
    command: migrate + runserver
    volumes: ../..:/app:cached
    ports: ["8000:8000"]
    depends_on: db (healthy)
    
  db:
    image: postgres:17
    healthcheck: pg_isready
    volumes: pg_data_dev
```

## Makefiles

Both `docker/prod/Makefile` and `docker/dev/Makefile` provide:

| Command | Description |
|---------|-------------|
| `make help` | Show available commands |
| `make build` | Build image with `--no-cache` |
| `make up` | Start containers with `-d --build` |
| `make down` | Stop containers |
| `make logs` | Follow logs (`-f`) |
| `make restart` | Down + Up |
| `make clean` | Remove containers, volumes, images, orphans |
| `make shell` | Exec bash in web container |
| `make migrate` | Run migrations in one-off container |

**Usage:** Run commands from respective `docker/prod/` or `docker/dev/` directories.

## Requirements (`docker/shared/requirements.txt`)

```
Django==6.0.4
django-ninja==1.6.2
djangorestframework==3.15.2
djangorestframework-simplejwt==5.4.0
psycopg2-binary==2.9.9
Pillow==10.4.0
pydantic==2.12.5
python-multipart==0.0.20
email-validator==2.2.0
gunicorn==22.0.0
uvicorn==0.34.0
```

## Environment Variables

### Production (`.env`)
```
DEBUG=False
SECRET_KEY=<production-secret>
ALLOWED_HOSTS=your-domain.com,www.your-domain.com
POSTGRES_DB=instrument_shop
POSTGRES_USER=instrument_shop_user
POSTGRES_PASSWORD=<strong-password>
DB_HOST=db
DB_PORT=5432
DJANGO_SETTINGS_MODULE=instrument_shop.settings
```

### Development (`.env`)
```
DEBUG=True
SECRET_KEY=django-insecure-dev-only-change-me
ALLOWED_HOSTS=localhost,127.0.0.1
POSTGRES_DB=instrument_shop_dev
POSTGRES_USER=instrument_shop_dev_user
POSTGRES_PASSWORD=instrument_shop_dev_pass
DB_HOST=db
DB_PORT=5432
DJANGO_SETTINGS_MODULE=instrument_shop.settings
```

## Nginx Configuration (`docker/prod/nginx/default.conf`)

- **Static files** (`/static/`): 7-day cache (604800s)
- **Media files** (`/media/`): 1-day cache (86400s)
- **Proxy** (`/`): Forwards to `http://web:8000` with proper headers
- **Client max body size**: 20MB

## Networks

Both environments use custom bridge network: `instrument-shop-network`

## Best Practices Implemented

1. ✅ Multi-stage builds (prod)
2. ✅ Alpine/slim base images (`python:3.12-slim`, `nginx:1.27-alpine`)
3. ✅ Non-root user execution (appuser)
4. ✅ Health checks for PostgreSQL
5. ✅ Named volumes for persistence
6. ✅ .dockerignore to reduce build context
7. ✅ `--no-cache-dir` for pip
8. ✅ Environment variables via `.env` files
9. ✅ `PYTHONDONTWRITEBYTECODE=1` and `PYTHONUNBUFFERED=1`
10. ✅ Cleanup apt cache after install

## Quick Start

### Development
```bash
cd docker/dev
cp .env.example .env
# Edit .env if needed
make build
make up
# Access at http://localhost:8000/api/
```

### Production
```bash
cd docker/prod
cp .env.example .env
# Edit .env with production values
make build
make up
# Access at http://localhost/api/
```

## Notes

- Dev compose overrides CMD to run migrations and use runserver
- Prod compose runs collectstatic before gunicorn
- Both use same `DJANGO_SETTINGS_MODULE=instrument_shop.settings`
- Database host is `db` (service name in compose)
- Static/media handling differs: nginx in prod, Django dev server in dev

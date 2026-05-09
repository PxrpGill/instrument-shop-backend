# План: Защита и стабилизация бекенда

## Обзор
Полный комплекс мер по защите API: rate limiting, Redis кэширование, security headers, CORS, production настройки.

## Задачи

### 1. Redis Infrastructure (Кэширование)
- [x] Добавить Redis в `docker/dev/docker-compose.yml`
- [x] Добавить `django-redis` в requirements.txt
- [x] Настроить `CACHES` в `settings.py` с Redis backend

### 2. Rate Limiting
- [x] Установить `django-ratelimit` (>=4.1)
- [x] Применить rate limits к endpoints:
  - `POST /customers/register` → 10 req/min на IP
  - `POST /customers/login` → 5 req/min на IP
  - `POST /customers/refresh` → 20 req/min на IP
  - Публичные GET → 100 req/min на IP
- [x] Добавить тесты для rate limiting

### 3. CORS Configuration
- [x] Установить `django-cors-headers`
- [x] Настроить `CORS_ALLOWED_ORIGINS` в settings
- [x] Ограничить `CORS_ALLOW_METHODS` и `CORS_ALLOW_HEADERS`

### 4. Security Headers (Nginx)
- [x] Добавить security headers в `docker/prod/nginx/default.conf`:
  - `X-Content-Type-Options: nosniff`
  - `X-Frame-Options: SAMEORIGIN`
  - `X-XSS-Protection: 1; mode=block`
  - `Referrer-Policy: strict-origin-when-cross-origin`
  - `Content-Security-Policy` (базовый)

### 5. Django Security Settings (Production)
- [x] Добавить в `settings.py`:
  - `SECURE_SSL_REDIRECT = True`
  - `SECURE_HSTS_SECONDS = 31536000`
  - `SECURE_HSTS_INCLUDE_SUBDOMAINS = True`
  - `SESSION_COOKIE_SECURE = True`
  - `CSRF_COOKIE_SECURE = True`
  - `SECURE_CONTENT_TYPE_NOSNIFF = True`
  - `X_FRAME_OPTIONS = 'SAMEORIGIN'`

### 6. Endpoint Caching
- [x] Добавить cache decorators для публичных endpoints:
  - `GET /public/categories/` → cache 5 min
  - `GET /public/products/` → cache 1 min (с vary_on_cookie)
  - `GET /public/products/{id}` → cache 5 min
- [x] Добавить cache invalidation при изменении products/categories
- [x] Добавить тесты для кэширования

### 7. Monitoring & Logging
- [x] Логирование rate limit violations (через django-ratelimit)
- [x] Логирование failed authentication attempts

## Файлы для изменения

| Файл | Изменения |
|------|-----------|
| `requirements.txt` | +django-ratelimit, +django-redis, +django-cors-headers |
| `docker/dev/docker-compose.yml` | +Redis service |
| `docker/prod/docker-compose.yml` | +Redis service |
| `docker/prod/nginx/default.conf` | +Security headers |
| `instrument_shop/settings.py` | +CACHES, +CORS, +Security settings |
| `apps/users/api/controllers.py` | +@ratelimit decorators |
| `apps/products/controllers.py` | +cache invalidation functions |
| `apps/products/public_api.py` | +@ratelimit +@vary_on_cookie + caching |
| `.env.example` | +REDIS_URL, +CORS_ALLOWED_ORIGINS |

## Тесты
- Тесты rate limiting для login/register endpoints
- Тесты cache hit/miss для публичных endpoints
- Все существующие тесты должны пройти (325+)

## Критерии завершения
1. [x] Redis запускается в Docker
2. [x] Rate limiting применяется к auth endpoints
3. [x] CORS настроен корректно
4. [x] Security headers добавлены в Nginx
5. [x] Публичные endpoints кэшируются
6. [ ] Все тесты проходят
7. [ ] `python -m black --check .` и `python -m flake8 .` проходят

# Instrument Shop Backend

REST API для интернет-магазина строительных инструментов, построенный на Django и Django Ninja.

## Технологический стек

- **Django 6.0.4** — веб-фреймворк
- **Django Ninja 1.6.2** — REST API фреймворк
- **PostgreSQL** — основная база данных (через Docker)
- **Pydantic 2.12.5** — валидация данных
- **Simple JWT** — аутентификация через JWT токены

## Структура проекта

```
instrument-shop-backend/
├── apps/
│   ├── products/           # Товары и категории
│   │   ├── models.py       # Модели: Category, Product, ProductImage
│   │   ├── controllers.py  # Внутренние API эндпоинты
│   │   ├── public_api.py   # Публичные эндпоинты для витрины
│   │   ├── schemas.py      # Pydantic схемы
│   │   └── services.py     # Бизнес-логика
│   ├── orders/             # Заказы
│   │   ├── models.py       # Модели: Order, OrderItem
│   │   ├── controllers.py  # API эндпоинты заказов
│   │   └── services.py     # Логика создания и управления заказами
│   └── users/              # Пользователи и роли
│       ├── models.py       # Модель Customer и Role
│       ├── constants.py    # Константы прав доступа
│       └── services/       # Сервисы аутентификации и ролей
├── core/                   # Вспомогательные утилиты и middleware
├── instrument_shop/        # Настройки Django и маршруты API
│   ├── settings.py         # Конфигурация проекта
│   ├── urls.py             # Маршрутизация URL
│   └── api.py              # Экземпляр Ninja API
├── docker/                 # Docker конфигурации
│   ├── dev/                # Окружение разработки
│   └── prod/               # Продакшн окружение
├── requirements.txt        # Зависимости Python
└── manage.py              # Скрипт управления Django
```

## Модели данных

### Пользователи (Customer)
- `id` — первичный ключ
- `email` — email (уникальный)
- `phone` — номер телефона
- `first_name`, `last_name` — имя и фамилия
- `address` — адрес доставки
- `roles` — связь с ролями (Many-to-Many)
- `is_active` — статус активности
- `created_at`, `updated_at` — временные метки

### Категории (Category)
- `id` — первичный ключ
- `name` — название категории (уникальное)
- `slug` — URL-дружественный slug (генерируется автоматически)
- `image` — изображение категории (опционально)
- `created_at`, `updated_at` — временные метки

### Товары (Product)
- `id` — первичный ключ
- `name` — название товара
- `description` — описание товара
- `parameters` — гибкое поле JSON для атрибутов (размер, цвет и т.д.)
- `price` — цена товара (Decimal)
- `sku` — артикул (уникальный)
- `brand` — бренд товара
- `status` — статус: `draft`, `published`, `archived`
- `availability` — доступность: `in_stock`, `out_of_stock`, `on_request`
- `categories` — связь с категориями (Many-to-Many)
- `created_at`, `updated_at` — временные метки

### Изображения товаров (ProductImage)
- `id` — первичный ключ
- `product` — связь с товаром (ForeignKey)
- `image` — изображение товара
- `alt_text` — альтернативный текст
- `is_primary` — флаг основного изображения
- `created_at`, `updated_at` — временные метки

### Заказы (Order)
- `id` — первичный ключ
- `customer` — покупатель (ForeignKey на Customer)
- `status` — статус: `new`, `processing`, `confirmed`, `cancelled`, `completed`
- `contact_email` — контактный email
- `contact_phone` — контактный телефон
- `first_name`, `last_name` — имя и фамилия получателя
- `address` — адрес доставки
- `notes` — примечания к заказу
- `total_amount` — общая сумма (вычисляемое поле)
- `created_at`, `updated_at` — временные метки

### Позиции заказа (OrderItem)
- `id` — первичный ключ
- `order` — связь с заказом (ForeignKey)
- `product` — связь с товаром (ForeignKey)
- `product_name` — снимок названия товара на момент заказа
- `quantity` — количество
- `unit_price` — снимок цены товара на момент заказа
- `subtotal` — подытог (вычисляемое поле)

## API Эндпоинты

### Аутентификация и пользователи (`/v1/customers/`)

| Метод | Эндпоинт | Описание | Права доступа |
|-------|----------|----------|---------------|
| POST | `/v1/customers/register` | Регистрация нового клиента | Гость |
| POST | `/v1/customers/login` | Вход в систему | Гость |
| POST | `/v1/customers/refresh` | Обновление токена | Гость |
| GET | `/v1/customers/me` | Профиль текущего клиента | Аутентифицированный |
| PATCH | `/v1/customers/me` | Обновление профиля | Аутентифицированный |
| POST | `/v1/customers/change-password` | Смена пароля | Аутентифицированный |

### Категории (`/v1/categories/`)

| Метод | Эндпоинт | Описание | Права доступа |
|-------|----------|----------|---------------|
| GET | `/v1/categories/` | Список всех категорий | view_category |
| POST | `/v1/categories/` | Создание категории | create_category |
| GET | `/v1/categories/{id}` | Получение категории по ID | view_category |
| PUT | `/v1/categories/{id}` | Обновление категории | edit_category |
| DELETE | `/v1/categories/{id}` | Удаление категории | delete_category |
| GET | `/v1/categories/{id}/products` | Товары в категории | view_product |

### Товары (внутренний API, `/v1/products/`)

| Метод | Эндпоинт | Описание | Права доступа |
|-------|----------|----------|---------------|
| GET | `/v1/products/` | Список всех товаров | view_product |
| POST | `/v1/products/` | Создание товара | create_product |
| GET | `/v1/products/{id}` | Получение товара по ID | view_product |
| PUT | `/v1/products/{id}` | Обновление товара | edit_product |
| POST | `/v1/products/{id}/publish` | Публикация товара | publish_product |
| DELETE | `/v1/products/{id}` | Удаление товара | delete_product |
| GET | `/v1/products/{id}/images` | Список изображений товара | view_product |
| POST | `/v1/products/{id}/images` | Добавление изображения | edit_product |
| PUT | `/v1/products/{id}/images/{img_id}` | Обновление изображения | edit_product |
| DELETE | `/v1/products/{id}/images/{img_id}` | Удаление изображения | edit_product |

### Заказы (`/v1/orders/`)

| Метод | Эндпоинт | Описание | Права доступа |
|-------|----------|----------|---------------|
| POST | `/v1/orders/` | Создание заказа | create_order |
| GET | `/v1/orders/` | Список заказов | Только персонал |
| GET | `/v1/orders/{id}` | Получение заказа | Владелец/Персонал |
| POST | `/v1/orders/{id}/cancel` | Отмена заказа | Владелец/Персонал |
| PUT | `/v1/orders/{id}/status` | Обновление статуса | manage_order_status |

### Публичная витрина (`/v1/public/`)

| Метод | Эндпоинт | Описание | Права доступа |
|-------|----------|----------|---------------|
| GET | `/v1/public/products/` | Публичный список товаров | Гость |
| GET | `/v1/public/products/{id}` | Публичный просмотр товара | Гость |
| GET | `/v1/public/categories/` | Публичный список категорий | Гость |

### Администрирование (`/v1/admin/`)

| Метод | Эндпоинт | Описание | Права доступа |
|-------|----------|----------|---------------|
| * | `/v1/admin/*` | Управление ролями и правами | Администратор |

### Проверка работоспособности

| Метод | Эндпоинт | Описание |
|-------|----------|----------|
| GET | `/hello` | Проверка API (health check) |

## Роли и права доступа

Система использует RBAC (Role-Based Access Control) с следующими ролями:

- **customer** — покупатель (создание заказов, управление своим профилем)
- **catalog_manager** — менеджер каталога (управление товарами и категориями, публикация)
- **admin** — администратор (полный доступ, управление ролями)

## Быстрый старт (Docker)

Проект использует Docker для развертывания. Все команды выполняются из директории `docker/dev`.

### Запуск в режиме разработки

```bash
cd docker/dev
cp .env.example .env

# Запуск контейнеров
make up

# Просмотр логов
make logs

# Выполнение миграций
make migrate

# Остановка
make down
```

**Особенности dev-окружения:**
- Django `runserver` с автоматической перезагрузкой (hot-reload)
- Код монтируется как volume — изменения применяются мгновенно
- PostgreSQL с проверкой готовности (healthcheck)
- Секреты читаются из `docker/dev/.env`

### Продакшн

```bash
cd docker/prod
cp .env.example .env

# Применение миграций
make migrate

# Запуск
make up
```

**Особенности prod-окружения:**
- Nginx как reverse proxy
- Gunicorn + Uvicorn workers (ASGI)
- Многоуровневая сборка Docker образа
- Статика и медиафайлы раздаются через Nginx

## Локальная разработка (без Docker)

### Установка зависимостей

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Настройка базы данных

```bash
python manage.py migrate
python manage.py createsuperuser
```

### Запуск сервера

```bash
python manage.py runserver
```

API будет доступно по адресу: `http://127.0.0.1:8000/api/`

## Тестирование

```bash
# Все тесты (через Docker)
docker-compose exec web pytest

# Тесты конкретного приложения
docker-compose exec web pytest apps/products/tests/ -v

# С покрытием
docker-compose exec web pytest --cov=apps
```

Текущий статус: **177 тестов проходят успешно**.

## Линтинг и форматирование

```bash
# Проверка форматирования
docker-compose exec web python -m black --check .
docker-compose exec web python -m isort --check-only .

# Автоформатирование
docker-compose exec web python -m black .
docker-compose exec web python -m isort .

# Проверка кода
docker-compose exec web python -m flake8 .
docker-compose exec web python -m mypy .
```

## Переменные окружения

Настройки хранятся в файлах `.env` в соответствующих директориях Docker:
- `docker/dev/.env` — для разработки
- `docker/prod/.env` — для продакшна

Шаблоны переменных находятся в файлах `.env.example`.

## Особенности реализации

1. **Публикация товаров**: Товары публикуются только через `POST /products/{id}/publish/` после проверки наличия названия, цены, изображения и категории.

2. **Защита от race conditions**: При создании заказа используется `select_for_update()` внутри транзакции для предотвращения гонки данных.

3. **Снимки данных**: При создании заказа сохраняются название и цена товара на момент заказа (независимо от будущих изменений товара).

4. **JWT аутентификация**: Используются JWT токены (access + refresh) через Simple JWT.

5. **Pydantic v2**: Схемы валидации используют Pydantic версии 2 с кастомными сериализаторами для Decimal, datetime и enum-полей.

## Лицензия

MIT

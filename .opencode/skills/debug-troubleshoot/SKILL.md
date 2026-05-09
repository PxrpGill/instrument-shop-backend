---
name: debug-troubleshoot
description: Expert guidance for diagnosing and fixing bugs in Django Ninja applications using logging, pdb, pytest, debug-toolbar, Silk, and Django shell
---

# Skill: debug-troubleshoot

**Назначение:** Диагностика и устранение багов в Django Ninja приложении

**Триггеры:** `ошибка`, `баг`, `проблема`, `debug`, `troubleshoot`, `не работает`, `500`, `exception`

**Инструменты:** Python logging, pdb/ipdb, pytest, django-debug-toolbar, Silk, Django shell

---

## Troubleshooting Flowchart

```
Проблема обнаружена
        │
        ▼
┌─────────────────┐
│ Классификация   │
│ - 500 Internal  │     ┌─────────────────┐
│ - 4xx Client    │────▶│ Логи приложения  │──▶ Читать логи
│ - Timeout       │     └─────────────────┘     (settings.LOGGING)
│ - Неожиданное   │
│   поведение     │
└─────────────────┘
        │
        ▼
┌─────────────────┐
│ Локализация     │
│ - Какая модель  │     ┌─────────────────┐
│ - Какой endpoint│───▶ │ Django shell    │──▶ Воспроизвести
│ - Какая операция│     └─────────────────┘     проблему
└─────────────────┘
        │
        ▼
┌─────────────────┐
│ Анализ          │
│ - Query/View    │     ┌─────────────────┐
│ - Model/Service │───▶ │ pytest -s -vv   │──▶ Точка останова
│ - Validation    │     └─────────────────┘
└─────────────────┘
        │
        ▼
┌─────────────────┐
│ Исправление     │
│ - Код           │
│ - Тест          │
│ - Документация  │
└─────────────────┘
```

---

## 1. Логирование (Python logging)

### Конфигурация Django settings

```python
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{levelname} {asctime} {module} {process:d} {thread:d} {message}",
            "style": "{",
        },
        "simple": {
            "format": "{levelname} {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
        "file": {
            "class": "logging.FileHandler",
            "filename": BASE_DIR / "logs" / "app.log",
            "formatter": "verbose",
        },
    },
    "loggers": {
        "django": {
            "handlers": ["console", "file"],
            "level": "INFO",
        },
        "apps": {
            "handlers": ["console", "file"],
            "level": "DEBUG",
            "propagate": False,
        },
    },
}
```

### Использование в коде

```python
import logging

logger = logging.getLogger(__name__)

class OrderService:
    def create_order(self, data: dict) -> Order:
        logger.debug("Creating order with data: %s", data)
        try:
            order = Order.objects.create(**data)
            logger.info("Order created: %s", order.id)
            return order
        except Exception as e:
            logger.error("Failed to create order: %s", str(e), exc_info=True)
            raise
```

### Контекстный логгер для request

```python
# middleware.py
import logging
import uuid

class RequestLoggingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request_id = str(uuid.uuid4())[:8]
        request.request_id = request_id
        
        logger = logging.getLogger("apps.requests")
        logger.info(
            "Request started",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.path,
                "user": getattr(request, "user", None),
            }
        )
        
        response = self.get_response(request)
        
        logger.info(
            "Request completed",
            extra={
                "request_id": request_id,
                "status_code": response.status_code,
                "duration_ms": response.duration_ms if hasattr(response, 'duration_ms') else None,
            }
        )
        return response
```

---

## 2. Интерактивная отладка (pdb/ipdb)

### Быстрый старт

```bash
# Установка
pip install ipdb

# Использование в коде
import ipdb; ipdb.set_trace()
```

### Команды pdb/ipdb

| Команда | Описание |
|---------|----------|
| `n` / `next` | Следующая строка |
| `s` / `step` | Шаг внутрь функции |
| `c` / `continue` | Продолжить выполнение |
| `b` / `break` | Установить breakpoint |
| `pp` | Красивый print объекта |
| `w` / `where` | Показать стек вызовов |
| `u` / `up` | Вверх по стеку |
| `d` / `down` | Вниз по стеку |
| `l` / `list` | Показать код вокруг |
| `a` / `args` | Аргументы текущей функции |

### Пример: отладка API endpoint

```python
# apps/orders/controllers.py
from django.db import transaction
import ipdb

class OrderController:
    @transaction.atomic
    def create_order(self, data: dict) -> Order:
        # Добавить breakpoint перед критической секцией
        ipdb.set_trace()
        
        # Проверить блокировку
        from django.db import connection
        print(connection.queries[-1])  # Последний SQL запрос
        
        products = data.pop('items', [])
        order = Order.objects.create(**data)
        
        for item in products:
            product = Product.objects.select_for_update().get(pk=item['product_id'])
            # Проверить состояние продукта
            ipdb.set_trace(context=5)  # Показать 5 строк контекста
            
            OrderItem.objects.create(
                order=order,
                product=product,
                quantity=item['quantity'],
                unit_price=product.price
            )
        
        return order
```

### pytest отладка

```bash
# Запуск с интерактивным отладчиком при падении
pytest -xvs --pdb --pdbcls=ipdb:ipdb.set_trace

# Остановиться на первом падении
pytest --pdb

# Внутри теста
def test_order_creation():
    import ipdb; ipdb.set_trace()
    # ... тестовый код
```

---

## 3. Django-debug-toolbar

### Установка

```bash
pip install django-debug-toolbar
```

### Настройка dev settings

```python
# settings.py
INSTALLED_APPS = [
    # ...
    "debug_toolbar",
]

MIDDLEWARE = [
    "debug_toolbar.middleware.DebugToolbarMiddleware",
    # ... другие middleware
]

INTERNAL_IPS = [
    "127.0.0.1",
]

DEBUG_TOOLBAR_CONFIG = {
    "SHOW_TOOLBAR_CALLBACK": lambda request: settings.DEBUG,
    "PANEL_OPTIONS": {
        "HISTORY": {"limit": 100},
    },
}
```

### Ключевые панели

| Панель | Информация |
|--------|------------|
| **History** | Все SQL запросы в хронологическом порядке |
| **SQL** | Текущие запросы с временем выполнения |
| **Templates** | Какие шаблоны рендерятся, контекст |
| **Signals** | Отправленные сигналы |
| **Cache** | Кэш операции |
| **Headers** | HTTP заголовки запроса/ответа |

### Анализ N+1 проблем

```python
# Открыть History panel - показаны ВСЕ запросы
# Искать повторяющиеся SELECT для одной таблицы

# Пример проблемы:
# SELECT * FROM products WHERE id = 1;
# SELECT * FROM products WHERE id = 2;
# SELECT * FROM products WHERE id = 3;

# Решение:
products = Product.objects.filter(id__in=[1, 2, 3]).select_related('category')
```

---

## 4. Silk (Profiling)

### Установка

```bash
pip install django-silk
```

### Настройка

```python
# settings.py
INSTALLED_APPS = [
    # ...
    "silk",
]

MIDDLEWARE = [
    "silk.middleware.SilkyMiddleware",
    # ... другие middleware
]

# settings.py
SILKY_PYTHON_PROFILER = True
SILKY_INTERCEPT_PERCENT = 100  # Ловить все запросы (для debugging)
```

### Использование

1. Запустить сервер: `python manage.py runserver`
2. Открыть: `http://localhost:8000/silk/`
3. Сделать запрос к API
4. Анализировать в Silk Dashboard:
   - Время выполнения endpoint
   - SQL запросы с timeline
   - Тело запроса/ответа

### Профилирование конкретного кода

```python
from silk.profiling.profiler import silk_profile

class ProductService:
    @silk_profile(name="Fetch products for order")
    def get_products_for_order(self, order_items: list) -> list:
        product_ids = [item['product_id'] for item in order_items]
        return Product.objects.filter(id__in=product_ids).select_related(
            'category', 'images'
        ).prefetch_related('tags')
```

---

## 5. Django Shell

### Интерактивная отладка

```bash
python manage.py shell
```

### Воспроизведение проблемы

```python
# Воспроизвести ошибку создания заказа
from apps.orders.services import OrderService

service = OrderService()

# Данные как в запросе
data = {
    'customer_id': 1,
    'contact_email': 'test@example.com',
    'contact_phone': '+79001234567',
    'delivery_address': 'ул. Пушкина, д.10',
    'items': [
        {'product_id': 1, 'quantity': 2},
    ]
}

# Выполнить
order = service.create_order(data)
```

### Проверка состояния

```python
# Проверить блокировки БД
from django.db import connection
from django.db.models import Q

# Есть ли товары в активных заказах?
OrderItem.objects.filter(
    order__status__in=['new', 'processing']
).values_list('product_id', flat=True).distinct()

# Проверить индексы
from django.db import connection
cursor = connection.cursor()
cursor.execute("SELECT * FROM pg_indexes WHERE tablename = 'orders_order'")
cursor.fetchall()

# Проверить connections
from django.db import connection
connection.ensure_connection()
print(f"Active connections: {len(connection.vendor)}")
```

---

## 6. Error Handling Patterns

### Гранулярный error handling

```python
# ✅ Правильно - специфичные exceptions
from django.db import IntegrityError, TransactionManagementError

class OrderService:
    def create_order(self, data: dict) -> Order:
        try:
            with transaction.atomic():
                order = Order.objects.create(customer=data['customer'])
                
                for item_data in data['items']:
                    product = Product.objects.select_for_update().get(
                        pk=item_data['product_id']
                    )
                    # Валидация stock
                    if product.stock < item_data['quantity']:
                        raise ValueError(
                            f"Insufficient stock for {product.name}. "
                            f"Available: {product.stock}, Requested: {item_data['quantity']}"
                        )
                    OrderItem.objects.create(
                        order=order,
                        product=product,
                        quantity=item_data['quantity'],
                        unit_price=product.price
                    )
                return order
                
        except IntegrityError as e:
            logger.error("Database integrity error: %s", str(e))
            raise OrderCreationError("Order cannot be created due to data conflict")
        except ValueError as e:
            logger.warning("Validation error: %s", str(e))
            raise
        except Exception as e:
            logger.exception("Unexpected error creating order")
            raise OrderCreationError("Unknown error occurred")
```

### Кастомные exceptions

```python
# apps/core/exceptions.py
class AppException(Exception):
    """Base exception for application"""
    def __init__(self, message: str, code: str = None):
        self.message = message
        self.code = code or "APP_ERROR"
        super().__init__(self.message)


class OrderCreationError(AppException):
    """Raised when order creation fails"""
    def __init__(self, message: str = "Failed to create order"):
        super().__init__(message, code="ORDER_CREATION_FAILED")


class ValidationError(AppException):
    """Raised when validation fails"""
    pass


# Использование в API
from ninja import HttpError

@api.post("/orders/")
def create_order(request, data: OrderCreateSchema):
    try:
        return order_service.create_order(data.dict())
    except OrderCreationError as e:
        raise HttpError(400, e.message)
```

---

## 7. Примеры диагностики

### Example 1: 500 ошибка на POST /v1/orders/

```
Workflow:
1. Читать логи: docker logs api | grep "500\|ERROR"
2. Найти traceback в логах
3. Определить строку с ошибкой
4. Воспроизвести в Django shell
5. Добавить breakpoint для анализа
```

**Лог:**
```
ERROR 2024-01-15 10:30:15 apps.orders.services OrderService.create_order
Traceback (most recent call last):
  File "/app/apps/orders/services.py", line 45, in create_order
    product = Product.objects.get(pk=item['product_id'])
  Product.DoesNotExist: Product matching query does not exist.
```

**Решение:**
```python
# Добавить exists() check перед get()
if not Product.objects.filter(pk=item['product_id']).exists():
    raise ValueError(f"Product {item['product_id']} does not exist")
```

---

### Example 2: Timeout на GET /v1/products/

```
Workflow:
1. Включить Silk профилирование
2. Запросить endpoint
3. Найти slowest queries в Silk Dashboard
4. Определить N+1 проблему
```

**Анализ Silk:**
```
Endpoint time: 4500ms
SQL queries: 156 (много!)
Slowest: SELECT * FROM products - 500ms each
```

**Решение:**
```python
# Было:
products = Product.objects.all()

# Стало:
products = Product.objects.select_related(
    'category'
).prefetch_related(
    'images', 'tags'
).filter(is_active=True)
```

---

### Example 3: Race condition при создании заказа

```
Workflow:
1. Проверить logs - заказы дублируются
2. Включить SQL logging
3. Воспроизвести с параллельными запросами
```

**Диагностика:**
```python
# В services.py - добавить логирование
import threading
import time

class OrderService:
    def create_order(self, data):
        thread_id = threading.current_thread().ident
        start_time = time.time()
        
        logger.debug(
            "Order creation started",
            extra={
                "thread_id": thread_id,
                "product_ids": [item['product_id'] for item in data['items']],
            }
        )
        
        # Критическая секция с блокировкой
        with transaction.atomic():
            # select_for_update предотвращает race condition
            for item in data['items']:
                Product.objects.select_for_update().get(pk=item['product_id'])
                # ...
```

---

## 8. Быстрые команды

```bash
# Логи Docker
docker logs -f api_container --tail 100

# Логи с grep
docker logs api_container 2>&1 | grep -E "ERROR|exception|Traceback"

# Django check
python manage.py check --deploy

# Django shell с автозагрузкой
python manage.py shell -c "from apps.orders.models import Order; print(Order.objects.count())"

# SQL в Django shell
from django.db import connection
connection.queries[-1]  # Последний запрос

# Проверить pending миграции
python manage.py showmigrations --plan

# Очистить кэш
python manage.py shell -c "from django.core.cache import cache; cache.clear()"
```

---

## Checklist при отладке

- [ ] Записан request_id для traceability
- [ ] Логи пишутся в правильный logger
- [ ] Sensitive data не попадает в логи
- [ ] Используется transaction.atomic() где нужно
- [ ] select_for_update() для блокировки строк
- [ ] Exception handling гранулярный
- [ ] Тест воспроизводит проблему
- [ ] Исправление покрыто тестом
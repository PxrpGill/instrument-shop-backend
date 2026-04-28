# План внедрения Unfold Admin Panel

## Обзор задачи
Внедрить современную тему Unfold для Django Admin в проект instrument-shop-backend. Unfold — это MIT-лицензированная тема, построенная на Tailwind CSS, которая заменяет стандартный интерфейс Django Admin на современный и функциональный.

## Текущее состояние
- В проекте **нет** файлов `admin.py` для приложений
- Модели определены в: `apps/users/models.py`, `apps/products/models.py`, `apps/orders/models.py`
- `INSTALLED_APPS` в `settings.py` не содержит unfold
- Статика настраивается через `STATIC_ROOT = BASE_DIR / 'staticfiles'`

## Детальный план

### 1. Обновление зависимостей
**Файлы для изменения:**
- `requirements.txt`
- `docker/shared/requirements.txt`

**Действия:**
Добавить `django-unfold` в список зависимостей:
```
django-unfold>=0.90.0
```

Установить в Docker контейнере:
```bash
docker-compose exec web pip install django-unfold
```

### 2. Настройка settings.py
**Файл:** `instrument_shop/settings.py`

**Изменения:**
В `INSTALLED_APPS` добавить `"unfold"` в самое начало (обязательно перед `django.contrib.admin`):
```python
INSTALLED_APPS = [
    "unfold",  # Обязательно перед django.contrib.admin
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "ninja",
    "rest_framework",
    "apps.users",
    "apps.products",
    "apps.orders",
]
```

### 3. Создание admin.py для приложений
Создать файлы `admin.py` в каждом приложении с регистрацией моделей через `unfold.admin.ModelAdmin`.

#### 3.1 apps/users/admin.py
```python
from unfold.admin import ModelAdmin
from django.contrib import admin
from apps.users.models import Role, CustomerRole, Customer

@admin.register(Role, CustomerRole, Customer)
class UserAdmin(ModelAdmin):
    pass
```

#### 3.2 apps/products/admin.py
```python
from unfold.admin import ModelAdmin
from django.contrib import admin
from apps.products.models import Category, Product, ProductImage

@admin.register(Category, Product, ProductImage)
class ProductAdmin(ModelAdmin):
    pass
```

#### 3.3 apps/orders/admin.py
```python
from unfold.admin import ModelAdmin
from django.contrib import admin
from apps.orders.models import Order, OrderItem

@admin.register(Order, OrderItem)
class OrderAdmin(ModelAdmin):
    pass
```

### 4. Сбор статических файлов
Unfold требует сбора статических файлов:
```bash
docker-compose exec web python manage.py collectstatic --noinput
```

### 5. Проверка работы
1. Запустить контейнеры (если не запущены):
   ```bash
   cd docker/dev
   docker-compose up -d
   ```

2. Создать суперпользователя (если нет):
   ```bash
   docker-compose exec web python manage.py createsuperuser
   ```

3. Перейти на `http://localhost:8000/admin/`

4. Проверить:
   - Современный интерфейс Unfold отображается
   - Все модели (Role, CustomerRole, Customer, Category, Product, ProductImage, Order, OrderItem) доступны в админ-панели
   - Тёмная/светлая тема переключается

## Порядок реализации
1. Обновить `requirements.txt` и `docker/shared/requirements.txt`
2. Установить `django-unfold` в контейнер
3. Изменить `instrument_shop/settings.py`
4. Создать `apps/users/admin.py`
5. Создать `apps/products/admin.py`
6. Создать `apps/orders/admin.py`
7. Выполнить `collectstatic`
8. Проверить работу админ-панели

## Файлы для изменения/создания
1. `requirements.txt` — добавить django-unfold
2. `docker/shared/requirements.txt` — добавить django-unfold
3. `instrument_shop/settings.py` — добавить unfold в INSTALLED_APPS
4. `apps/users/admin.py` — создать новый файл
5. `apps/products/admin.py` — создать новый файл
6. `apps/orders/admin.py` — создать новый файл

## Критерии завершения
- [ ] Unfold успешно установлен и отображается на `/admin/`
- [ ] Все 8 моделей зарегистрированы и доступны в админ-панели
- [ ] Статика успешно собрана (`collectstatic` без ошибок)
- [ ] Интерфейс имеет современный вид (Tailwind CSS)
- [ ] Тёмная тема работает
- [ ] Тесты проходят: `docker-compose exec web pytest`
- [ ] Линтинг проходит: `docker-compose exec web python -m black --check . && python -m isort --check-only .`

## Дополнительные возможности (опционально)
После базовой настройки можно добавить:
- Кастомный дашборд с виджетами статистики
- Настройку бокового меню (сгруппировать по приложениям)
- Кастомные фильтры и действия
- Unfold Studio для визуальной настройки (платный плагин)

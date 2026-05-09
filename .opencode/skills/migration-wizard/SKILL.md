---
name: migration-wizard
description: Safe creation and management of Django migrations including schema changes, data migrations, rollbacks, and zero-downtime strategies
---

# Skill: migration-wizard

**Назначение:** Безопасное создание и управление Django миграциями

**Триггеры:** `migration`, `миграция`, `мигрировать`, `makemigrations`, `migrate`, `schema`, `база данных`

**Инструменты:** Django migrate system, sqlmigrate, ShowMigration, Rollback

---

## Troubleshooting Flowchart

```
Миграция needed
        │
        ▼
┌─────────────────────────┐
│ Тип миграции            │
│ ┌─────────┐ ┌─────────┐  │
│ │Schema   │ │Data     │  │
│ │Alter    │ │Update   │  │
│ └────┬────┘ └────┬────┘  │
└──────┼──────────┼───────┘
       │          │
       ▼          ▼
┌───────────┐ ┌───────────┐
│ Проверка  │ │ Проверка  │
│ --dry-run │ │ Backup    │
│ --check   │ │ Rollback  │
└─────┬─────┘ └─────┬─────┘
       │          │
       ▼          ▼
┌───────────┐ ┌───────────┐
│ Schema    │ │ Data      │
│ Migration │ │ Migration │
│ (auto)    │ │ (manual)  │
└─────┬─────┘ └─────┬─────┘
       │          │
       ▼          ▼
┌─────────────────────────┐
│ Применение              │
│ 1. Docker exec          │
│ 2. CI/CD pipeline       │
│ 3. Backup после         │
└─────────────────────────┘
```

---

## 1. Безопасные Schema миграции

### Предварительная проверка

```bash
# Проверка pending миграций
python manage.py showmigrations

# Проверка без применения (dry-run)
python manage.py migrate --check

# Посмотреть SQL перед применением
python manage.py sqlmigrate app_name migration_name
```

### Безопасные операции

#### Добавление поля с DEFAULT

```python
# ❌ Опасно - длительная блокировка таблицы
# migrations/bad.py
migrations.AddField(
    model_name='order',
    name='priority',
    field=models.IntegerField(default=1),  # DEFAULT в schema - блокировка всей таблицы
)

# ✅ Безопасно - отдельная операция для default
# migrations/good.py
operations = [
    migrations.AddField(
        model_name='order',
        name='priority',
        field=models.IntegerField(null=True, blank=True),  # Без default
    ),
    migrations.RunPython(
        code=lambda apps, schema: apps.get_model('orders', 'Order').objects.update(priority=1),
        reverse_code=lambda apps, schema: None,  # Необратимое изменение
    ),
    migrations.AlterField(
        model_name='order',
        name='priority',
        field=models.IntegerField(default=1, null=False),  # Добавляем default после заполнения
    ),
]
```

#### Добавление NOT NULL поля

```python
# Безопасная последовательность для добавления NOT NULL колонки
operations = [
    # Шаг 1: Добавить nullable поле
    migrations.AddField(
        model_name='order',
        name='external_id',
        field=models.CharField(max_length=64, null=True, blank=True),
    ),
    # Шаг 2: Заполнить существующие записи
    migrations.RunPython(
        code=lambda apps, schema: apps.get_model('orders', 'Order').objects.update(
            external_id=apps.get_model('orders', 'Order').objects.values_list('id', flat=True)
        ),
    ),
    # Шаг 3: Установить NOT NULL constraint
    migrations.AlterField(
        model_name='order',
        name='external_id',
        field=models.CharField(max_length=64, null=False, blank=False),
    ),
]
```

#### Удаление поля

```python
# ✅ Всегда сначала nullable, затем удаление
# Шаг 1: Сделать nullable
migrations.AlterField(
    model_name='order',
    name='old_field',
    field=models.CharField(max_length=100, null=True),
)
# Шаг 2: Подождать deploy
# Шаг 3: Удалить
migrations.RemoveField(
    model_name='order',
    name='old_field',
)
```

### Переименование

```python
# Безопасное переименование без потери данных
operations = [
    migrations.RenameField(
        model_name='order',
        old_name='customer_name',
        new_name='contact_name',
    ),
]
```

---

## 2. Data миграции (RunPython)

### Структура Data Migration

```python
# apps/orders/migrations/0003_backfill_tracking.py
from django.db import migrations
import logging

logger = logging.getLogger(__name__)

def fill_tracking_number(apps, schema_editor):
    """Заполнить tracking_number для существующих заказов"""
    Order = apps.get_model('orders', 'Order')
    
    # Используем bulk_update для производительности
    orders_to_update = []
    count = 0
    
    for order in Order.objects.filter(
        tracking_number__isnull=True,
        status__in=['processing', 'shipped']
    ).iterator(chunk_size=1000):
        order.tracking_number = f"TRK-{order.id:08d}"
        orders_to_update.append(order)
        count += 1
        
        if len(orders_to_update) >= 500:
            Order.objects.bulk_update(orders_to_update, ['tracking_number'])
            logger.info(f"Updated {count} orders")
            orders_to_update = []
    
    if orders_to_update:
        Order.objects.bulk_update(orders_to_update, ['tracking_number'])
    
    logger.info(f"Total orders updated: {count}")


def reverse_fill(apps, schema_editor):
    """Откат - очистить tracking_number"""
    Order = apps.get_model('orders', 'Order')
    Order.objects.filter(tracking_number__startswith='TRK-').update(tracking_number=None)


class Migration(migrations.Migration):
    dependencies = [
        ('orders', '0002_add_tracking'),
    ]

    operations = [
        migrations.RunPython(
            code=fill_tracking_number,
            reverse_code=reverse_fill,
        ),
    ]
```

### Миграция с консистентностью данных

```python
def migrate_product_categories(apps, schema_editor):
    """Обновить категории продуктов"""
    Product = apps.get_model('products', 'Product')
    Category = apps.get_model('products', 'Category')
    
    # Создать категорию по умолчанию если не существует
    default_cat, _ = Category.objects.get_or_create(
        slug='uncategorized',
        defaults={
            'name': 'Без категории',
            'is_active': True,
        }
    )
    
    # Обновить продукты без категории
    updated = Product.objects.filter(category__isnull=True).update(
        category=default_cat
    )
    
    logger.info(f"Assigned {updated} products to default category")
    
    # Проверить консистентность
    orphaned = Product.objects.filter(category__isnull=True).count()
    if orphaned > 0:
        logger.warning(f"Found {orphaned} orphaned products")
```

### Конкурентная миграция

```python
def migrate_with_lock(apps, schema_editor):
    """Миграция с блокировкой для предотвращения race condition"""
    from django.db import transaction
    
    with transaction.atomic():
        # Получить эксклюзивную блокировку таблицы
        schema_editor.execute(
            "LOCK TABLE orders_order IN EXCLUSIVE MODE"
        )
        
        Order = apps.get_model('orders', 'Order')
        total = Order.objects.count()
        
        # Массовое обновление
        Order.objects.filter(status='new').update(
            priority=1
        )
        Order.objects.filter(status='processing').update(
            priority=2
        )
        
        logger.info(f"Migrated {total} orders")
```

---

## 3. Rollback стратегии

### Отмена миграции

```bash
# Отменить одну миграцию назад
python manage.py migrate app_name 000X_previous_migration

# Показать что будет отменено
python manage.py showmigrations app_name  # + в status означает применено

# Откатить все миграции приложения
python manage.py migrate app_name zero
```

### Ручной rollback

```python
# Миграция с безопасным rollback
def migrate_add_field(apps, schema_editor):
    # Forward - добавить поле
    schema_editor.add_field(
        Order,
        schema_editor.add_field(
            Order._meta.get_field('metadata'),
            # ...
        )
    )

def rollback_add_field(apps, schema_editor):
    # Reverse - удалить поле
    schema_editor.remove_field(
        Order._meta.get_field('metadata'),
    )

class Migration(migrations.Migration):
    # ...
    operations = [
        migrations.RunPython(
            code=migrate_add_field,
            reverse_code=rollback_add_field,
        ),
    ]
```

### Restore данных

```bash
# Backup перед миграцией (PostgreSQL)
pg_dump -h $DB_HOST -U $DB_USER $DB_NAME > backup_pre_migration.sql

# Restore
psql -h $DB_HOST -U $DB_USER $DB_NAME < backup_pre_migration.sql
```

### Zero-downtime миграция

```python
# Для больших таблиц - неблокирующая миграция

class Migration(migrations.Migration):
    atomic = False  # Позволяет частичное применение
    
    operations = [
        # Фаза 1: Добавить колонку (без constraints)
        migrations.AddField(
            model_name='product',
            name='metadata_json',
            field=models.JSONField(null=True),
        ),
        # Фаза 2: Фоновое обновление (через Celery или management command)
        migrations.RunPython(
            code=lambda apps, schema: None,  # Celery job сделает эту работу
        ),
        # Фаза 3: Добавить constraint после обновления всех записей
        migrations.RunSQL(
            sql="ALTER TABLE products_product ALTER COLUMN metadata_json SET NOT NULL",
            reverse_sql="ALTER TABLE products_product ALTER COLUMN metadata_json DROP NOT NULL",
        ),
    ]
```

---

## 4. Индексы и constraints

### Создание индексов

```python
# Безопасное добавление индекса
operations = [
    migrations.AddIndex(
        model_name='order',
        index=models.Index(
            fields=['status', 'created_at'],
            name='order_status_created_idx',
        ),
    ),
]

# Index для часто фильтруемых полей
operations = [
    migrations.AddIndex(
        model_name='product',
        index=models.Index(
            fields=['category', 'is_published'],
            name='product_category_published_idx',
        ),
    ),
    # Partial index (PostgreSQL)
    migrations.RunSQL(
        sql="CREATE INDEX product_active_idx ON products_product (created_at) WHERE is_published = true",
        reverse_sql="DROP INDEX product_active_idx",
    ),
]
```

### Проверка индексов

```python
# Посмотреть существующие индексы
from django.db import connection

with connection.cursor() as cursor:
    cursor.execute("""
        SELECT indexname, indexdef 
        FROM pg_indexes 
        WHERE tablename = 'orders_order'
    """)
    for row in cursor.fetchall():
        print(row)
```

### Удаление индексов

```python
# Безопасное удаление индекса
operations = [
    migrations.RunSQL(
        sql="DROP INDEX IF EXISTS product_old_index",
        reverse_sql="CREATE INDEX product_old_index ON products_product (old_field)",
    ),
]
```

---

## 5. Примеры команд

### Полезные команды

```bash
# Создать миграцию
python manage.py makemigrations app_name

# Миграция с описанием
python manage.py makemigrations app_name --name descriptive_name

# Показать SQL без применения
python manage.py sqlmigrate orders 0003_update_status

# Применить все миграции
python manage.py migrate

# Применить конкретную
python manage.py migrate orders 0003_update_status

# Показать статус миграций
python manage.py showmigrations

# Fake миграция (если данные уже в БД)
python manage.py migrate app_name 0003_update_status --fake

# Fake initial (для существующих таблиц)
python manage.py migrate app_name --fake-initial
```

### CI/CD миграции

```bash
#!/bin/bash
# deploy.sh

set -e

echo "=== Migration: $(date) ==="

# Backup
pg_dump -h $DB_HOST -U $DB_USER $DB_NAME > backup_$(date +%Y%m%d_%H%M%S).sql

# Check pending
python manage.py showmigrations | grep "\[ ]" || echo "No pending migrations"

# Apply
python manage.py migrate --noinput

# Verify
python manage.py check --deploy

echo "=== Done ==="
```

### Docker exec

```bash
# Внутри контейнера
docker exec -it instrument-shop-backend-api-1 python manage.py migrate

# С указанием app
docker exec -it instrument-shop-backend-api-1 python manage.py migrate orders

# Dry run
docker exec -it instrument-shop-backend-api-1 python manage.py migrate --check
```

---

## 6. Шаблоны миграций

### Template: Добавить enum поле

```python
# migrations/0004_add_order_priority.py
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('orders', '0003_add_tracking'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='priority',
            field=models.IntegerField(
                choices=[(1, 'Низкий'), (2, 'Средний'), (3, 'Высокий')],
                default=1,
            ),
        ),
    ]
```

### Template: Добавить FK с default

```python
# migrations/0005_add_default_category.py
from django.db import migrations, models


def create_default_category(apps, schema):
    Category = apps.get_model('products', 'Category')
    Category.objects.get_or_create(
        slug='default',
        defaults={'name': 'По умолчанию', 'is_active': True}
    )


class Migration(migrations.Migration):
    dependencies = [
        ('products', '0004_add_category'),
    ]

    operations = [
        migrations.RunPython(create_default_category),
        migrations.AddField(
            model_name='product',
            name='category',
            field=models.ForeignKey(
                on_delete=models.SET_DEFAULT,
                to='products.Category',
                default=None,  # Установится после создания
            ),
        ),
    ]
```

### Template: Изменить поле

```python
# migrations/0006_extend_email_field.py
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('orders', '0005_add_default_category'),
    ]

    operations = [
        migrations.AlterField(
            model_name='order',
            name='contact_email',
            field=models.EmailField(max_length=254),
        ),
    ]
```

---

## 7. Troubleshooting

### Завислая миграция

```bash
# Найти заблокированные таблицы
docker exec -it postgres psql -U postgres -d instrument_shop -c "
SELECT blocked.pid, blocked.query, blocking.pid AS blocking_pid, blocking.query AS blocking_query
FROM pg_stat_activity AS blocked
JOIN pg_stat_activity AS blocking ON blocking.pid = ANY(pg_blocking_pids(blocked.pid))
WHERE blocked.state = 'active'
AND blocked.query LIKE '%migration%'
"

# Kill завиший процесс
docker exec -it postgres psql -U postgres -d instrument_shop -c "SELECT pg_terminate_backend(PID)"
```

### Duplicate key violation

```python
# При миграции данных
def merge_duplicates(apps, schema):
    Product = apps.get_model('products', 'Product')
    
    # Найти дубликаты
    duplicates = Product.objects.values('sku').annotate(
        count=models.Count('id')
    ).filter(count__gt=1)
    
    for dup in duplicates:
        sku = dup['sku']
        products = Product.objects.filter(sku=sku).order_by('created_at')
        primary = products.first()
        
        # Merge все связанные записи к первому
        for product in products[1:]:
            # Обновить FK в заказах
            OrderItem.objects.filter(product=product).update(product=primary)
            product.delete()
```

### Конфликт миграций

```python
# Если два разработчика создали миграции с одинаковым depends
# Вручную объединить зависимости

class Migration(migrations.Migration):
    dependencies = [
        # Объединить зависимости
        ('orders', '0003_update_status'),
        ('orders', '0004_another_update'),  # Добавить зависимость
    ]
```

---

## 8. Checklist перед миграцией

- [ ] Создан backup базы данных
- [ ] Проверены pending миграции: `showmigrations`
- [ ] SQL проверен: `sqlmigrate`
- [ ] Модель актуальна для всех env (dev/staging/prod)
- [ ] Data migration имеет reverse_code
- [ ] Большие таблицы используют chunk_size
- [ ] Index добавляется отдельно от ALTER
- [ ] Zero-downtime для high-traffic таблиц
- [ ] Проверить foreign key constraints
- [ ] Протестировать rollback процедуру
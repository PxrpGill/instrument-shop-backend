# RBAC System Logic Documentation

## Overview
Система ролевого доступа (RBAC) для интернет-магазина музыкальных инструментов.

---

## 1. Архитектура данных

### Модели

#### Role
```
Role
 ├── name (varchar 50, unique, indexed)          # 'customer', 'manager', 'admin'
 ├── description (text, blank)
 ├── permissions (JSONField, default={})          # {'create_product': true, '*': true}
 ├── is_active (boolean, default=true)            # soft delete
 ├── created_at (datetime, auto_now_add)
 └── updated_at (datetime, auto_now)
```

**Методы:**
- `has_permission(perm: str) -> bool` — проверяет разрешение (wildcard `*` = всё)
- `get_all_permissions() -> dict` — возвращает копию пермишенов

#### CustomerRole (through)
```
CustomerRole
 ├── customer (FK → Customer, on_delete=CASCADE)
 ├── role (FK → Role, on_delete=CASCADE)
 ├── assigned_at (datetime, auto_now_add)
 └── assigned_by (FK → Customer, null, on_delete=SET_NULL)  # кто назначил
```

**Constraints:**
- `unique_together = (customer, role)`
- Индексы: customer, role, assigned_at

#### Customer (расширен)
```
Customer (наследуется от base)
 ├── id (UUID, PK)
 ├── email (unique, indexed)
 ├── phone (indexed)
 ├── first_name, last_name, address
 ├── password_hash
 ├── roles (M2M ↔ Role через CustomerRole)
 ├── is_active (default=true)
 ├── created_at, updated_at
 └── last_login (null)
```

**Новые методы:**
- `has_role(role_name: str) -> bool` — есть ли у клиента роль (кэшируется через prefetch)
- `has_permission(permission: str) -> bool` — есть ли разрешение через любую из ролей
- `get_roles() -> QuerySet[Role]` — список ролей клиента
- `get_permissions() -> dict` — агрегирует все разрешения из всех ролей (поздние перезаписывают ранние)

---

## 2. Разрешения (Permissions)

### Структура
Разрешения хранятся в JSONField как простой dict:
```python
{
  "view_product": true,
  "create_product": false,
  "edit_product": true,
  "*": false  # wildcard - все разрешения
}
```

### Проверка разрешений

**В модели Role:**
```python
def has_permission(self, permission: str) -> bool:
    if '*' in self.permissions:
        return True
    return self.permissions.get(permission, False)
```

**В модели Customer:**
```python
def has_permission(self, permission: str) -> bool:
    for role in self.roles.filter(is_active=True):
        if role.has_permission(permission):
            return True
    return False
```

**В RoleService:**
```python
@staticmethod
def has_permission(customer: Customer, permission: str) -> bool:
    if customer.has_role('admin'):  # админ всегда имеет всё
        return True
    return customer.has_permission(permission)
```

### Агрегация
Когда у клиента несколько ролей, разрешения **объединяются** (any role grants permission). Если разные роли дают conflicting значения для одного permission, **последняя загруженная роль** побеждает (потому что `dict.update()`).

---

## 3. Стандартные роли (Default Roles)

Создаются автоматически миграцией `0003_default_roles`.

| Роль | Разрешения |
|------|------------|
| `customer` | `view_product`, `view_category`, `view_own_profile`, `edit_own_profile` |
| `manager` | `view_product`, `create_product`, `edit_product`, `delete_product`, `view_category`, `create_category`, `edit_category`, `delete_category`, `view_customer` |
| `admin` | `*` (wildcard — абсолютно всё) |

---

## 4. JWT + Роли

### Генерация токенов (`CustomerService.generate_tokens`)

```python
refresh = RefreshToken()
refresh['user_id'] = str(customer.id)
refresh['email'] = customer.email
refresh['roles'] = list(customer.roles.filter(is_active=True).values_list('name', flat=True))
refresh['permissions'] = {}  # aggregated from roles
refresh['is_admin'] = customer.has_role('admin')
```

Access token автоматически наследует все custom claims от refresh.

### Аутентификация (`CustomerJWTAuthentication`)

```python
def get_user(self, validated_token):
    customer = Customer.objects.select_related('roles').prefetch_related('roles').get(
        id=user_id, is_active=True
    )
    # Прикрепляем объект к request
    request.customer = customer
    return customer
```

---

## 5. Защита эндпоинтов

### Паттерн 1: Inline-проверка (products/controllers.py)

```python
@router.post("/products/")
def create_product(request, payload: ProductCreateSchema):
    HasRoleMixin.require_permission(request.customer, 'create_product')
    # ... business logic
```

`HasRoleMixin.require_permission()` выбрасывает `PermissionDeniedError` (403), если:
- не админ (has_role('admin')) И
- у клиента нет указанного пермишена

### Паттерн 2: Админ-эндпоинты (role_controllers.py)

```python
def require_admin(request: HttpRequest) -> Customer:
    customer = get_customer_from_request(request)
    if not customer.has_role('admin'):
        raise PermissionDeniedError("Требуется роль администратора")
    return customer

@router.get("/admin/roles/")
def list_roles(request):
    require_admin(request)  # первая строка
    return RoleService.get_all_roles()
```

---

## 6. Сервисный слой

### RoleService

#### Основные операции

**Чтение:**
- `get_role_by_name(name)` → Role | None
- `get_role_by_id(id)` → Role | None
- `get_all_roles()` → List[Role]
- `get_customer_roles(customer)` → List[Role]
- `get_customer_permissions(customer)` → dict
- `get_customers_with_role(role_name)` → List[Customer]

**Запись:**
- `create_role(name, permissions, description, created_by)` → Role
- `update_role(role, permissions, description)` → Role
- `delete_role(role)` → bool (soft delete, is_active=False)

**Назначение:**
- `assign_role(customer, role_name, assigned_by)` → CustomerRole
  - Проверяет дубли (± UniqueConstraint)
  - Создает связь
- `remove_role(customer, role_name, removed_by)` → bool
  - Удаляет связь

**Проверки:**
- `has_role(customer, role_name)` → bool
- `has_permission(customer, permission)` → bool (админы всегда True)
- `require_role(customer, *roles)` → bool | raises InsufficientPrivilegesError
- `require_permission(customer, *perms, require_all=True)` → bool | raises PermissionDeniedError
- `initialize_default_roles()` → dict (создает 3 стандартные роли)

---

## 7. Поток выполнения запроса

### Пример: POST /api/v1/products/ (создание товара)

1. **Django Ninja** получает запрос
2. **JWT Authentication** (`CustomerJWTAuthentication.authenticate()`):
   - Извлекает bearer token
   - Декодирует, получает `user_id`
   - Загружает `Customer` с prefetch_related('roles')
   - Прикрепляет `request.customer = customer`
3. **Эндпоинт** `create_product` вызывается
4. **Внутри эндпоинта:**
   ```python
   HasRoleMixin.require_permission(request.customer, 'create_product')
   ```
5. **Логика проверки:**
   - Если `customer.has_role('admin')` → сразу True (админ-байпас)
   - Иначе для каждой роли клиента: `role.has_permission('create_product')`
   - Если ни одна роль не даёт разрешение → `PermissionDeniedError` (HTTP 403)
6. **Если разрешение есть** → создаём продукт

---

## 8. Автоматическое назначение ролей

### При регистрации (`/api/v1/customers/register`)

```python
customer = CustomerService.create_customer(...)
# Автоматически назначаем роль 'customer'
try:
    RoleService.assign_role(customer, 'customer')
except Exception:
    pass  # если роль ещё нет (будет создана миграцией)
```

### При логине — только аутентификация, роли уже в БД

---

## 9. Админ-панель (Управление ролями)

Эндпоинты под `/api/v1/admin/`:

| Метод | Путь | Описание | Доступ |
|-------|------|----------|--------|
| GET | `/roles/` | список всех ролей | `admin` |
| GET | `/roles/{id}/` | детали роли | `admin` |
| POST | `/roles/` | создать роль | `admin` |
| PUT | `/roles/{id}/` | обновить роль | `admin` |
| DELETE | `/roles/{id}/` | деактивировать роль | `admin` (кроме системных) |
| GET | `/customers/{id}/roles/` | роли клиента | `admin` |
| POST | `/customers/{id}/roles/` | назначить роль | `admin` |
| DELETE | `/customers/{id}/roles/{role_name}/` | удалить роль | `admin` (не свою admin) |
| GET | `/customers/{id}/permissions/` | все пермишены клиента | `admin` |

---

## 10. Кэширование ролей

Роли подгружаются через `prefetch_related('roles')` при аутентификации. Это избегает N+1 запросов. В JWT также закэшированы `roles` и `permissions` для быстрых проверок в follow-up запросах (но мы всё равно лезем в БД при каждой проверке).

---

## 11. Важные ограничения

- **Лестница привилегий:** customer < manager < admin
- **Админ байпас:** `if customer.has_role('admin'): return True` везде
- **Системные роли:** `admin`, `customer` нельзя удалить (soft delete), только деактивировать
- **Самоуничтожение:** админ не может удалить у себя роль `admin` (защита от потери доступа)
- **Регистрация:** автоматически получает `customer` (минимальные права)
- **Деактивация роли:** `is_active=False` сохраняет историю, но исчезает из `get_roles()`

---

## 12. Миграции

1. **0002_rbac.py** — создаёт `Role`, `CustomerRole`, добавляет M2M `Customer.roles`
2. **0003_default_roles.py** — вставляет 3 стандартные роли

После миграции в БД будут:
```sql
roles: ('customer', 'manager', 'admin')
customer_roles: NULL (пока не будет назначено)
```

---

## 13. Примеры использования

### Как проверить роль в API:

```python
# Verbose way (inline)
HasRoleMixin.require_permission(request.customer, 'edit_product')

# Or programmatically in service
if RoleService.has_permission(customer, 'delete_product'):
    # allow
```

### Как назначить роль (админ):

```bash
POST /api/v1/admin/customers/{customer_id}/roles/
{
  "role_name": "manager"
}
```

### Как получить роли клиента:

```bash
GET /api/v1/admin/customers/{customer_id}/roles/
```

### Как проверить роли в коде (модель):

```python
customer = Customer.objects.get(email='...')
if customer.has_role('admin'):
    # do admin stuff
```

---

## 14. Ошибки и исключения

| Исключение | HTTP-код | Сценарий |
|------------|----------|----------|
| `PermissionDeniedError` | 403 | Нет нужной роли/пермишена |
| `RoleNotFoundError` | 404 | Роль или клиент не найден |
| `CustomerRoleAssignmentError` | 400 | Роль уже назначена / дубликат |
| `InsufficientPrivilegesError` | 403 | Требуется более высокая роль |

---

## 15. Расширение системы

### Добавление новой роли

```python
RoleService.create_role(
    name='content_moderator',
    description='Может редактировать товары, но не удалять',
    permissions={
        'view_product': True,
        'edit_product': True,
        'delete_product': False,
    }
)
```

### Добавление пермишена в существующую роль

```python
role = RoleService.get_role_by_name('manager')
role.permissions['delete_product'] = True
role.save()
```

### Миграция существующих пользователей

Существующие клиенты после миграции **не получают роли автоматически**. Нужно:
```python
for customer in Customer.objects.all():
    RoleService.assign_role(customer, 'customer')
```
Можно сделать data migration.

---

## 16. Потенциальные проблемы

1. **N+1 при проверке `customer.has_permission()`** — каждый вызов ходит в роли. Решение: prefetch_related на этапе аутентификации.
2. **Динамические изменения ролей в токене** — если role изменился, JWT всё ещё хранит старые роли. Решение: короткий TTL access токена (15 min) + принудиный logout.
3. **Race condition при создании дубликатов роли** — UniqueConstraint в БД, но лучше ловить `IntegrityError`.
4. **Каскадное удаление** — удаление роли каскадно удалит все CustomerRole (что хорошо для soft-delete истории?).
5. **Зависимость от строковых имён ролей** — опечатка в коде = runtime error. Лучше использовать константы/Enum.

---

## 17. Дальнейшее улучшение

- [ ] Константы ролей и пермишенов в `core/constants.py`
- [ ] Caching permissions per user (Redis) с invalidation при изменении роли
- [ ] AJAX-friendly errors с полным списком доступных пермишенов
- [ ] Встроенная проверка пермишенов в Django Ninja через кастомный `permission_class` вместо ручных `require_permission`
- [ ] Реализация scoped permissions (например, `edit_own_product` vs `edit_any_product`)
- [ ] Аудит-логи: кто и когда назначал роли

---

**Версия:** 1.0  
**Последнее обновление:** 2026-04-24

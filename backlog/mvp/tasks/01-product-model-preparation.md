# 01 Product Model Preparation

### BE-001 Add product status field

**Goal:** добавить жизненный цикл товара в модель `Product`.

**Implementation scope:**
- добавить поле статуса в `apps/products/models.py`;
- определить enum/choices: `draft`, `published`, `archived`;
- задать `draft` как значение по умолчанию;
- создать миграцию.

**Done when:**
- новые товары создаются со статусом `draft`;
- миграция применяется без ручных правок;
- статус доступен в ORM и admin/API слое.

**Depends on:** none

### BE-002 Add product availability field

**Goal:** добавить признак доступности товара.

**Implementation scope:**
- добавить поле availability в `Product`;
- определить enum/choices: `in_stock`, `out_of_stock`, `on_request`;
- выбрать дефолтное значение;
- создать миграцию.

**Done when:**
- у каждого товара есть availability;
- поле сохраняется и читается через ORM;
- миграция создана.

**Depends on:** none

### BE-003 Add SKU field to product

**Goal:** добавить артикул товара.

**Implementation scope:**
- добавить поле `sku` в `Product`;
- определить ограничения: уникальность, nullable/blank;
- создать миграцию.

**Done when:**
- товар хранит SKU;
- в модели зафиксированы правила валидации;
- миграция создана.

**Depends on:** none

### BE-004 Add brand field to product

**Goal:** добавить бренд товара как базовый атрибут MVP.

**Implementation scope:**
- добавить строковое поле `brand` в `Product`;
- создать миграцию;
- пока не создавать отдельную модель бренда.

**Done when:**
- бренд сохраняется в товаре;
- поле доступно в create/update/read сценариях.

**Depends on:** none

### BE-005 Expose new product fields in schemas

**Goal:** синхронизировать новые поля товара со схемами API.

**Implementation scope:**
- обновить `apps/products/schemas.py`;
- добавить `status`, `availability`, `sku`, `brand` в read schema;
- добавить допустимые поля в create/update schema;
- решить, какие поля может менять staff API.

**Done when:**
- API схемы принимают и возвращают новые поля;
- сериализация не ломает существующие тесты.

**Depends on:** `BE-001`, `BE-002`, `BE-003`, `BE-004`


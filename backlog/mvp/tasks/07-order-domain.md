# 07 Order Domain ✅

### BE-021 Create order model

**Goal:** добавить сущность заказа.

**Implementation scope:**
- создать модель `Order`;
- добавить owner/customer relation;
- добавить контакты заказчика;
- добавить статус заказа;
- добавить timestamps;
- создать миграцию.

**Done when:**
- `Order` существует как ORM сущность;
- у заказа есть статус и контакты;
- миграция создана.

**Depends on:** none

### BE-022 Create order item model

**Goal:** добавить позиции заказа.

**Implementation scope:**
- создать модель `OrderItem`;
- связать с `Order` и `Product`;
- хранить quantity;
- хранить snapshot полей товара, минимум `product_name` и `unit_price`;
- создать миграцию.

**Done when:**
- заказ может содержать позиции;
- цена товара фиксируется в позиции;
- миграция создана.

**Depends on:** `BE-021`

### BE-023 Add order status choices

**Goal:** формализовать статусы заказа.

**Implementation scope:**
- определить enum/choices: `new`, `processing`, `confirmed`, `cancelled`, `completed`;
- выбрать дефолтный статус.

**Done when:**
- статус заказа ограничен допустимыми значениями;
- новый заказ создаётся в `new`.

**Depends on:** `BE-021`

### BE-024 Create order schemas

**Goal:** описать API-схемы для создания и чтения заказа.

**Implementation scope:**
- добавить request/response schemas;
- описать payload для order items;
- скрыть внутренние поля, если они не нужны клиенту.

**Done when:**
- есть отдельные схемы для customer API и staff API, если это нужно;
- сериализация заказа работает корректно.

**Depends on:** `BE-021`, `BE-022`, `BE-023`


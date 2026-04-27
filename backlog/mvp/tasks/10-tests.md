# 10 Tests

### BE-031 Add tests for public catalog visibility

**Goal:** зафиксировать публичные правила выдачи каталога.

**Implementation scope:**
- протестировать, что `draft` не виден публично;
- протестировать, что `archived` не виден публично;
- протестировать, что `published` виден публично.

**Done when:**
- visibility rules покрыты тестами.

**Depends on:** `BE-012`, `BE-013`

### BE-032 Add tests for staff catalog permissions

**Goal:** зафиксировать права сотрудников на управление каталогом.

**Implementation scope:**
- тесты на create/update/delete category/product;
- тесты на смену статуса товара;
- тесты на недостаточные permissions.

**Done when:**
- RBAC-поведение каталога покрыто тестами.

**Depends on:** `BE-017`, `BE-018`, `BE-020`

### BE-033 Add tests for order creation flow

**Goal:** проверить основной customer flow заказа.

**Implementation scope:**
- успешное создание заказа;
- запрет заказа неопубликованного товара;
- фиксация цены в позиции;
- валидация количества.

**Done when:**
- основной order flow покрыт тестами.

**Depends on:** `BE-025`, `BE-026`, `BE-027`

### BE-034 Add tests for staff order management

**Goal:** проверить внутреннюю обработку заказов.

**Implementation scope:**
- доступ staff к списку и карточке заказа;
- смена статуса заказа;
- отказ доступа без permissions.

**Done when:**
- staff order API покрыт тестами.

**Depends on:** `BE-028`, `BE-029`, `BE-030`


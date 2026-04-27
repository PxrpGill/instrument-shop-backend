# 08 Customer Order API ✅

### BE-025 Create customer order endpoint

**Goal:** дать покупателю возможность создать заказ.

**Implementation scope:**
- добавить endpoint создания заказа;
- принять товар, количество и контакты;
- создать `Order` и `OrderItem` в транзакции.

**Done when:**
- заказ создаётся одним запросом;
- transaction гарантирует целостность данных.

**Depends on:** `BE-021`, `BE-022`, `BE-024`

### BE-026 Snapshot product price at order creation

**Goal:** гарантировать фиксацию цены на момент заказа.

**Implementation scope:**
- при создании `OrderItem` копировать цену товара;
- не читать цену динамически из `Product` после заказа;
- покрыть тестом.

**Done when:**
- изменение цены товара после заказа не меняет старый заказ;
- тест это подтверждает.

**Depends on:** `BE-022`, `BE-025`

### BE-027 Restrict order creation to published products

**Goal:** не позволять заказывать черновики и архивные товары.

**Implementation scope:**
- проверить статус товара при создании заказа;
- вернуть понятную ошибку API.

**Done when:**
- заказ создаётся только для `published` товара;
- негативный сценарий покрыт тестом.

**Depends on:** `BE-001`, `BE-025`


# 09 Staff Order API ✅

### BE-028 Create staff orders list endpoint

**Goal:** дать сотрудникам просмотр входящих заказов.

**Implementation scope:**
- добавить staff endpoint списка заказов;
- подгружать customer и order items оптимизированно;
- защитить endpoint permissions.

**Done when:**
- сотрудник с нужной ролью видит список заказов;
- покупатель или гость доступ не получают.

**Depends on:** `BE-021`, `BE-022`, `BE-023`

### BE-029 Create staff order detail endpoint

**Goal:** дать сотрудникам просмотр одного заказа.

**Implementation scope:**
- добавить detail endpoint заказа;
- вернуть состав заказа и контакты клиента;
- защитить endpoint permissions.

**Done when:**
- staff может получить карточку заказа;
- неавторизованный пользователь доступ не получает.

**Depends on:** `BE-028`

### BE-030 Create order status update endpoint

**Goal:** дать сотрудникам возможность менять статус заказа.

**Implementation scope:**
- добавить endpoint смены статуса;
- ограничить набор допустимых статусов;
- покрыть тестом.

**Done when:**
- статус меняется через backend API;
- недопустимые значения отклоняются.

**Depends on:** `BE-023`, `BE-029`


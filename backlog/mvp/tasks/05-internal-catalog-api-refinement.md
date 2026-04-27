# 05 Internal Catalog API Refinement ✅

### BE-016 Separate public and internal product routers

**Goal:** развести storefront API и staff API по разным роутерам.

**Implementation scope:**
- отделить публичные endpoint'ы от внутренних CRUD endpoint'ов;
- сделать структуру понятной для дальнейшего роста.

**Done when:**
- код публичных и внутренних endpoint'ов не смешан;
- права доступа читаются прозрачно.

**Depends on:** `BE-011`, `BE-012`, `BE-013`

### BE-017 Allow staff to manage product status

**Goal:** дать сотруднику возможность менять статус товара через внутренний API.

**Implementation scope:**
- обновить staff update flow;
- разрешить изменение `status`;
- встроить publish validation.

**Done when:**
- `catalog_manager` или `admin` могут менять статус товара;
- публикация проходит через backend-валидацию.

**Depends on:** `BE-005`, `BE-007`

### BE-018 Allow staff to manage product availability

**Goal:** дать сотруднику возможность менять availability товара.

**Implementation scope:**
- обновить create/update сценарии staff API;
- покрыть тестом изменение availability.

**Done when:**
- availability редактируется через внутренний API;
- изменение защищено permission-check.

**Depends on:** `BE-005`


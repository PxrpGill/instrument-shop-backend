# 06 RBAC Hardening ✅

### BE-019 Centralize permission constants

**Goal:** убрать строки permissions, разбросанные по коду.

**Implementation scope:**
- создать единое место для permission constants;
- перевести контроллеры и сервисы на константы.

**Done when:**
- ключевые permissions объявлены централизованно;
- прямые строковые литералы больше не дублируются без необходимости.

**Depends on:** none

### BE-020 Review and update default roles

**Goal:** привести роли MVP к фактическим потребностям backend.

**Implementation scope:**
- проверить текущие миграции ролей;
- закрепить набор permissions для `customer`, `catalog_manager`, `admin`;
- обновить data migration или seeding logic.

**Done when:**
- роли создаются с нужным набором permissions;
- тесты или миграционные проверки это подтверждают.

**Depends on:** `BE-019`


# 02 Publication Rules

### BE-006 Define publishable product rules in code

**Goal:** формализовать, когда товар можно перевести в `published`.

**Implementation scope:**
- определить обязательные поля для публикации;
- выбрать место логики: model/service/validator;
- реализовать проверку publish readiness.

**Done when:**
- есть единая backend-проверка publishability;
- правило не дублируется хаотично по контроллерам.

**Depends on:** `BE-001`, `BE-002`, `BE-003`, `BE-004`

### BE-007 Prevent publishing incomplete product

**Goal:** запретить публикацию невалидного товара.

**Implementation scope:**
- встроить проверку в update/publish сценарий;
- вернуть понятную ошибку API при попытке публикации;
- покрыть негативный сценарий тестом.

**Done when:**
- неполный товар нельзя перевести в `published`;
- API отдаёт предсказуемую ошибку.

**Depends on:** `BE-006`

### BE-008 Enforce at least one image for published product

**Goal:** запретить публикацию товара без изображений.

**Implementation scope:**
- включить наличие хотя бы одного `ProductImage` в publish rules;
- покрыть сценарий тестом.

**Done when:**
- товар без изображения не публикуется;
- тест это подтверждает.

**Depends on:** `BE-006`

### BE-009 Enforce category presence for published product

**Goal:** запретить публикацию товара без категорий.

**Implementation scope:**
- включить наличие хотя бы одной категории в publish rules;
- покрыть сценарий тестом.

**Done when:**
- товар без категории не публикуется;
- тест это подтверждает.

**Depends on:** `BE-006`


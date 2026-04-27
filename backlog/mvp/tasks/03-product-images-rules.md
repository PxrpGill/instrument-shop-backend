# 03 Product Images Rules

### BE-010 Ensure single primary image per product

**Goal:** у товара не должно быть более одного primary image.

**Implementation scope:**
- определить механизм: model validation, save override или service rule;
- обеспечить консистентность при create/update image;
- покрыть тестами.

**Done when:**
- для одного товара одновременно существует максимум одно `is_primary=True`;
- поведение подтверждено тестами.

**Depends on:** none


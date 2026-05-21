# Product Description Repeater Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Заменить `Product.description_parameters` JSONField на реляционную модель-repeater: `ProductDescriptionSection` (секции) → `ProductDescriptionItem` (пункты: название + значение).

**Architecture:** Создаём две новые модели в `apps/products`, переносим данные data-миграцией, обновляем admin (nested inline через show_change_link по паттерну HomePageShowcase), обновляем API-сериализатор и admin-схемы, удаляем старый JSONField.

**Tech Stack:** Django 6.0, django-unfold, django-ninja, pytest-django

---

## File Map

| Файл | Действие |
|------|---------|
| `apps/products/models.py` | добавить `ProductDescriptionSection`, `ProductDescriptionItem`; удалить `_sanitize_description_parameters` |
| `apps/products/migrations/0010_product_description_section.py` | schema migration (генерируется) |
| `apps/products/migrations/0011_migrate_description_parameters.py` | data migration (создать вручную) |
| `apps/products/migrations/0012_remove_description_parameters.py` | удалить JSONField (генерируется) |
| `apps/products/admin.py` | добавить `ProductDescriptionSectionAdmin`, `ProductDescriptionSectionInline`, `ProductDescriptionItemInline` |
| `apps/products/catalog_serializers.py` | заменить `_serialize_description_parameters` |
| `apps/products/schemas.py` | убрать `description_parameters` из схем |
| `apps/products/tests/test_catalog.py` | обновить `test_returns_description_and_tech_specs` |
| `apps/products/tests/test_product_description.py` | создать (тесты новых моделей) |

---

## Task 1: Создать новые модели и тесты

**Files:**
- Modify: `apps/products/models.py`
- Create: `apps/products/tests/test_product_description.py`

- [ ] **Step 1: Написать failing-тесты**

  Создать файл `apps/products/tests/test_product_description.py`:

  ```python
  """Тесты модели ProductDescriptionSection / ProductDescriptionItem."""
  import pytest

  from apps.products.models import (
      Product,
      ProductDescriptionItem,
      ProductDescriptionSection,
      ProductStatusChoices,
  )

  pytestmark = pytest.mark.django_db


  @pytest.fixture
  def product():
      return Product.objects.create(
          name="Дрель",
          price=5000,
          status=ProductStatusChoices.PUBLISHED,
      )


  class TestProductDescriptionSection:
      def test_create_section(self, product):
          section = ProductDescriptionSection.objects.create(
              product=product,
              title="Общие характеристики",
              order=0,
          )
          assert section.pk is not None
          assert str(section) == "Общие характеристики"

      def test_sections_ordered_by_order(self, product):
          ProductDescriptionSection.objects.create(product=product, title="B", order=2)
          ProductDescriptionSection.objects.create(product=product, title="A", order=1)
          titles = list(
              ProductDescriptionSection.objects.filter(product=product).values_list("title", flat=True)
          )
          assert titles == ["A", "B"]

      def test_cascade_delete_with_product(self, product):
          section = ProductDescriptionSection.objects.create(
              product=product, title="Секция", order=0
          )
          ProductDescriptionItem.objects.create(section=section, name="K", value="V", order=0)
          product.delete()
          assert ProductDescriptionSection.objects.count() == 0
          assert ProductDescriptionItem.objects.count() == 0


  class TestProductDescriptionItem:
      def test_create_item(self, product):
          section = ProductDescriptionSection.objects.create(
              product=product, title="Электрика", order=0
          )
          item = ProductDescriptionItem.objects.create(
              section=section,
              name="Напряжение",
              value="220 В",
              order=0,
          )
          assert item.pk is not None
          assert str(item) == "Напряжение: 220 В"

      def test_items_ordered_by_order(self, product):
          section = ProductDescriptionSection.objects.create(
              product=product, title="S", order=0
          )
          ProductDescriptionItem.objects.create(section=section, name="B", value="b", order=2)
          ProductDescriptionItem.objects.create(section=section, name="A", value="a", order=1)
          names = list(
              ProductDescriptionItem.objects.filter(section=section).values_list("name", flat=True)
          )
          assert names == ["A", "B"]
  ```

- [ ] **Step 2: Запустить — должен упасть**

  ```bash
  cd docker/dev && docker compose run --rm web pytest apps/products/tests/test_product_description.py -v
  ```

  Ожидаемый результат: `ImportError` — `ProductDescriptionSection` не существует.

- [ ] **Step 3: Добавить модели в `apps/products/models.py`**

  В конец файла (после `ProductImage`) добавить:

  ```python
  class ProductDescriptionSection(TimeStampedModel):
      """Секция описания товара (внешний repeater)."""

      product = models.ForeignKey(
          Product,
          on_delete=models.CASCADE,
          related_name="description_sections",
          verbose_name="Товар",
      )
      title = models.CharField(max_length=255, verbose_name="Название секции")
      order = models.PositiveIntegerField(default=0, verbose_name="Порядок")

      class Meta:
          verbose_name = "Секция описания"
          verbose_name_plural = "Секции описания"
          ordering = ["order"]

      def __str__(self) -> str:
          return self.title


  class ProductDescriptionItem(TimeStampedModel):
      """Пункт секции описания товара (внутренний repeater)."""

      section = models.ForeignKey(
          ProductDescriptionSection,
          on_delete=models.CASCADE,
          related_name="items",
          verbose_name="Секция",
      )
      name = models.CharField(max_length=255, verbose_name="Название")
      value = models.TextField(verbose_name="Значение")
      order = models.PositiveIntegerField(default=0, verbose_name="Порядок")

      class Meta:
          verbose_name = "Пункт секции"
          verbose_name_plural = "Пункты секции"
          ordering = ["order"]

      def __str__(self) -> str:
          return f"{self.name}: {self.value}"
  ```

- [ ] **Step 4: Запустить — должны пройти**

  ```bash
  cd docker/dev && docker compose run --rm web pytest apps/products/tests/test_product_description.py -v
  ```

  Ожидаемый результат: `5 passed` (миграция ещё не создана — тест упадёт с `OperationalError`, перейти к Task 2 и вернуться).

  > Примечание: если тест упадёт с `OperationalError: table does not exist` — это нормально. Продолжить с Task 2 (создать миграцию), затем вернуться и прогнать тест снова.

---

## Task 2: Schema migration

**Files:**
- Create: `apps/products/migrations/0010_product_description_section.py` (генерируется)

- [ ] **Step 1: Сгенерировать миграцию**

  ```bash
  cd docker/dev && docker compose run --rm web python manage.py makemigrations products --name product_description_section
  ```

  Ожидаемый результат: создан файл `apps/products/migrations/0010_product_description_section.py` с двумя операциями `CreateModel`.

- [ ] **Step 2: Применить миграцию**

  ```bash
  cd docker/dev && docker compose run --rm web python manage.py migrate
  ```

  Ожидаемый результат: `OK`.

- [ ] **Step 3: Запустить тесты новых моделей**

  ```bash
  cd docker/dev && docker compose run --rm web pytest apps/products/tests/test_product_description.py -v
  ```

  Ожидаемый результат: `5 passed`.

- [ ] **Step 4: Commit**

  ```bash
  git add apps/products/models.py apps/products/migrations/0010_product_description_section.py apps/products/tests/test_product_description.py
  git commit -m "feat: добавить модели ProductDescriptionSection и ProductDescriptionItem"
  ```

---

## Task 3: Data migration

**Files:**
- Create: `apps/products/migrations/0011_migrate_description_parameters.py`

- [ ] **Step 1: Создать пустую data migration**

  ```bash
  cd docker/dev && docker compose run --rm web python manage.py makemigrations products --empty --name migrate_description_parameters
  ```

  Ожидаемый результат: создан `apps/products/migrations/0011_migrate_description_parameters.py`.

- [ ] **Step 2: Заполнить data migration**

  Открыть созданный файл и заменить содержимое на:

  ```python
  from django.db import migrations
  import html


  def _strip_html(text: str) -> str:
      """Удалить HTML-теги и декодировать entities."""
      import re
      clean = re.sub(r"<[^>]+>", " ", text or "")
      clean = html.unescape(clean)
      return " ".join(clean.split()).strip()


  def migrate_forward(apps, schema_editor):
      Product = apps.get_model("products", "Product")
      ProductDescriptionSection = apps.get_model("products", "ProductDescriptionSection")
      ProductDescriptionItem = apps.get_model("products", "ProductDescriptionItem")

      for product in Product.objects.exclude(description_parameters=[]):
          blocks = product.description_parameters
          if not isinstance(blocks, list):
              continue
          for idx, block in enumerate(blocks):
              if not isinstance(block, dict):
                  continue
              title = str(block.get("title") or "").strip()
              parameters_html = str(block.get("parameters") or "").strip()
              if not title and not parameters_html:
                  continue
              section = ProductDescriptionSection.objects.create(
                  product=product,
                  title=title or "Без названия",
                  order=idx,
              )
              stripped = _strip_html(parameters_html)
              if stripped:
                  ProductDescriptionItem.objects.create(
                      section=section,
                      name="Описание",
                      value=stripped,
                      order=0,
                  )


  def migrate_backward(apps, schema_editor):
      ProductDescriptionSection = apps.get_model("products", "ProductDescriptionSection")
      ProductDescriptionSection.objects.all().delete()


  class Migration(migrations.Migration):
      dependencies = [
          ("products", "0010_product_description_section"),
      ]

      operations = [
          migrations.RunPython(migrate_forward, migrate_backward),
      ]
  ```

- [ ] **Step 3: Применить data migration**

  ```bash
  cd docker/dev && docker compose run --rm web python manage.py migrate
  ```

  Ожидаемый результат: `OK`.

- [ ] **Step 4: Commit**

  ```bash
  git add apps/products/migrations/0011_migrate_description_parameters.py
  git commit -m "feat: data migration — перенести description_parameters в ProductDescriptionSection"
  ```

---

## Task 4: Обновить ProductAdmin

**Files:**
- Modify: `apps/products/admin.py`

- [ ] **Step 1: Добавить импорт новых моделей**

  В `apps/products/admin.py` изменить строку импорта моделей:

  ```python
  from apps.products.models import (
      Category,
      Product,
      ProductDescriptionItem,
      ProductDescriptionSection,
      ProductImage,
  )
  ```

- [ ] **Step 2: Добавить inlines для repeater**

  После класса `ProductImageInline` добавить:

  ```python
  class ProductDescriptionItemInline(TabularInline):
      model = ProductDescriptionItem
      extra = 0
      fields = ("name", "value", "order")
      ordering = ("order",)
      verbose_name = "Пункт"
      verbose_name_plural = "Пункты"


  @admin.register(ProductDescriptionSection, site=admin.site)
  class ProductDescriptionSectionAdmin(ModelAdmin):
      list_display = ("title", "product", "order")
      list_filter = ("product",)
      search_fields = ("title", "product__name")
      ordering = ("product", "order")
      inlines = [ProductDescriptionItemInline]
      autocomplete_fields = ("product",)


  class ProductDescriptionSectionInline(TabularInline):
      model = ProductDescriptionSection
      extra = 0
      fields = ("title", "order")
      show_change_link = True
      ordering = ("order",)
      verbose_name = "Секция описания"
      verbose_name_plural = "Секции описания"
  ```

- [ ] **Step 3: Обновить `ProductAdmin.fieldsets` и inlines**

  В `ProductAdmin` заменить `inlines` и убрать `description_parameters` из fieldsets:

  ```python
  @admin.register(Product, site=admin.site)
  class ProductAdmin(ModelAdmin):
      list_display = ("name", "brand", "price", "status", "availability", "created_at")
      list_filter = ("status", "availability", "categories", "brand")
      search_fields = ("name", "sku", "brand", "description")
      filter_horizontal = ("categories",)
      ordering = ("-created_at",)
      list_editable = ("status", "availability")
      inlines = [ProductImageInline, ProductDescriptionSectionInline]
      fieldsets = (
          (
              "Основное",
              {
                  "fields": (
                      "name",
                      "sku",
                      "brand",
                      "description",
                      "categories",
                  ),
              },
          ),
          (
              "Цена и доступность",
              {"fields": ("price", "status", "availability")},
          ),
          (
              "Параметры карточки",
              {
                  "fields": (
                      "parameters",
                      "technical_specifications",
                  ),
                  "classes": ("collapse",),
              },
          ),
      )
  ```

- [ ] **Step 4: Commit**

  ```bash
  git add apps/products/admin.py
  git commit -m "feat: добавить ProductDescriptionSection admin с nested inline"
  ```

---

## Task 5: Обновить catalog_serializers.py и тесты

**Files:**
- Modify: `apps/products/catalog_serializers.py`
- Modify: `apps/products/tests/test_catalog.py`

- [ ] **Step 1: Написать failing-тест**

  В `apps/products/tests/test_catalog.py` найти метод `test_returns_description_and_tech_specs` (строка ~285) и заменить его:

  ```python
  def test_returns_description_sections(self, client, published_product):
      from apps.products.models import ProductDescriptionItem, ProductDescriptionSection

      section = ProductDescriptionSection.objects.create(
          product=published_product,
          title="Общие характеристики",
          order=0,
      )
      ProductDescriptionItem.objects.create(
          section=section,
          name="Тип",
          value="дрель",
          order=0,
      )
      ProductDescriptionItem.objects.create(
          section=section,
          name="Мощность",
          value="650 Вт",
          order=1,
      )

      response = client.get(f"/catalog/products/{published_product.id}")
      product = response.json()["product"]
      assert product["descriptionParameters"] == [
          {
              "title": "Общие характеристики",
              "items": [
                  {"name": "Тип", "value": "дрель"},
                  {"name": "Мощность", "value": "650 Вт"},
              ],
          }
      ]

  def test_returns_tech_specs(self, client, published_product):
      published_product.technical_specifications = [
          {
              "title": "Электрика",
              "specifications": [
                  {"label": "Напряжение", "value": "220 В"},
              ],
          }
      ]
      published_product.save()

      response = client.get(f"/catalog/products/{published_product.id}")
      product = response.json()["product"]
      assert product["techicalSpecifications"] == [
          {
              "title": "Электрика",
              "specifications": [
                  {"label": "Напряжение", "value": "220 В"},
              ],
          }
      ]
  ```

  Также обновить `test_happy_path` — убрать проверку `"descriptionParameters" not in product` (или оставить как есть, оба варианта корректны, пока нет секций).

- [ ] **Step 2: Запустить — должен упасть**

  ```bash
  cd docker/dev && docker compose run --rm web pytest apps/products/tests/test_catalog.py::TestProductDetail::test_returns_description_sections -v
  ```

  Ожидаемый результат: `FAILED` — сериализатор всё ещё читает `description_parameters`.

- [ ] **Step 3: Обновить `catalog_serializers.py`**

  В `apps/products/catalog_serializers.py`:

  1. Убрать импорт `Product` из секции где используется `description_parameters` (он остаётся для остального кода).

  2. В `serialize_product_detail` заменить блок с `description_parameters`:

  ```python
  def serialize_product_detail(
      product: Product, request: Optional[HttpRequest] = None
  ) -> dict:
      detail: dict = {
          "id": product.id,
          "title": product.name,
          "description": product.description or "",
          "price": _price_to_int(product),
          "status": serialize_status(product),
          "category": serialize_categories(product.categories.all()),
      }
      if product.sku:
          detail["sku"] = product.sku

      gallery = _gallery_pictures(product, request)
      if gallery:
          detail["gallery"] = gallery

      description_parameters = _serialize_description_sections(product)
      if description_parameters:
          detail["descriptionParameters"] = description_parameters

      technical_specifications = _serialize_technical_specifications(
          product.technical_specifications or []
      )
      if technical_specifications:
          detail["techicalSpecifications"] = technical_specifications

      return detail
  ```

  3. Заменить функцию `_serialize_description_parameters` на `_serialize_description_sections`:

  ```python
  def _serialize_description_sections(product: Product) -> list[dict]:
      out: list[dict] = []
      for section in product.description_sections.prefetch_related("items").all():
          items = [
              {"name": item.name, "value": item.value}
              for item in section.items.all()
          ]
          if items:
              out.append({"title": section.title, "items": items})
      return out
  ```

- [ ] **Step 4: Запустить тест — должен пройти**

  ```bash
  cd docker/dev && docker compose run --rm web pytest apps/products/tests/test_catalog.py -v
  ```

  Ожидаемый результат: все тесты `passed`.

- [ ] **Step 5: Commit**

  ```bash
  git add apps/products/catalog_serializers.py apps/products/tests/test_catalog.py
  git commit -m "feat: обновить catalog serializer — читать description_sections вместо description_parameters JSON"
  ```

---

## Task 6: Обновить admin schemas.py

**Files:**
- Modify: `apps/products/schemas.py`

- [ ] **Step 1: Добавить схемы для новых моделей и убрать `description_parameters`**

  Заменить содержимое `apps/products/schemas.py`:

  ```python
  """Схемы внутреннего admin API товаров."""

  from typing import Optional

  from ninja import ModelSchema

  from .models import (
      Category,
      Product,
      ProductDescriptionItem,
      ProductDescriptionSection,
      ProductImage,
  )


  class CategorySchema(ModelSchema):
      class Meta:
          model = Category
          fields = ["id", "slug", "name", "poster", "created_at", "updated_at"]


  class CategoryCreateSchema(ModelSchema):
      class Meta:
          model = Category
          fields = ["name", "poster"]


  class ProductImageSchema(ModelSchema):
      class Meta:
          model = ProductImage
          fields = ["id", "image", "is_primary", "order", "created_at", "updated_at"]


  class ProductImageCreateSchema(ModelSchema):
      class Meta:
          model = ProductImage
          fields = ["image", "is_primary", "order"]


  class ProductDescriptionItemSchema(ModelSchema):
      class Meta:
          model = ProductDescriptionItem
          fields = ["id", "name", "value", "order"]


  class ProductDescriptionSectionSchema(ModelSchema):
      items: list[ProductDescriptionItemSchema] = []

      class Meta:
          model = ProductDescriptionSection
          fields = ["id", "title", "order", "created_at", "updated_at"]


  class ProductSchema(ModelSchema):
      categories: Optional[list[CategorySchema]] = []
      images: Optional[list[ProductImageSchema]] = []
      description_sections: Optional[list[ProductDescriptionSectionSchema]] = []

      class Meta:
          model = Product
          fields = [
              "id",
              "name",
              "description",
              "parameters",
              "technical_specifications",
              "price",
              "sku",
              "brand",
              "status",
              "availability",
              "categories",
              "created_at",
              "updated_at",
          ]


  class ProductCreateSchema(ModelSchema):
      category_ids: Optional[list[int]] = []

      class Meta:
          model = Product
          fields = [
              "name",
              "description",
              "parameters",
              "technical_specifications",
              "price",
              "sku",
              "brand",
              "availability",
          ]


  class ProductUpdateSchema(ModelSchema):
      class Meta:
          model = Product
          fields = [
              "name",
              "description",
              "parameters",
              "technical_specifications",
              "price",
              "sku",
              "brand",
              "availability",
          ]
  ```

- [ ] **Step 2: Запустить все тесты**

  ```bash
  cd docker/dev && docker compose run --rm web pytest -v
  ```

  Ожидаемый результат: все тесты `passed`.

- [ ] **Step 3: Commit**

  ```bash
  git add apps/products/schemas.py
  git commit -m "feat: обновить admin-схемы Product — убрать description_parameters, добавить description_sections"
  ```

---

## Task 7: Удалить description_parameters JSONField

**Files:**
- Modify: `apps/products/models.py`
- Create: `apps/products/migrations/0012_remove_description_parameters.py` (генерируется)

- [ ] **Step 1: Удалить поле и функцию санитизации из models.py**

  В `apps/products/models.py`:

  1. Удалить поле `description_parameters` из класса `Product` (строки ~80-88).

  2. В методе `Product.save()` удалить вызов `_sanitize_description_parameters`:

  ```python
  def save(self, *args, **kwargs):
      super().save(*args, **kwargs)
  ```

  3. Удалить функцию `_sanitize_description_parameters` (строки ~157-169).

- [ ] **Step 2: Сгенерировать миграцию**

  ```bash
  cd docker/dev && docker compose run --rm web python manage.py makemigrations products --name remove_description_parameters
  ```

  Ожидаемый результат: создан файл `apps/products/migrations/0012_remove_description_parameters.py` с операцией `RemoveField`.

- [ ] **Step 3: Применить миграцию**

  ```bash
  cd docker/dev && docker compose run --rm web python manage.py migrate
  ```

  Ожидаемый результат: `OK`.

- [ ] **Step 4: Запустить все тесты**

  ```bash
  cd docker/dev && docker compose run --rm web pytest -v
  ```

  Ожидаемый результат: все тесты `passed`.

- [ ] **Step 5: Commit**

  ```bash
  git add apps/products/models.py apps/products/migrations/0012_remove_description_parameters.py
  git commit -m "feat: удалить description_parameters JSONField из Product"
  ```

---

## Task 8: Финальная проверка

- [ ] **Step 1: Запустить dev-сервер**

  ```bash
  cd docker/dev && docker compose up -d
  ```

- [ ] **Step 2: Проверить admin товара**

  Перейти на `http://localhost:8000/admin/products/product/`. Открыть любой товар. Убедиться:
  - нет поля `description_parameters` (JSONField удалён)
  - есть секция "Секции описания" с кнопкой "Изменить" рядом с каждой секцией
  - при переходе на секцию — виден inline с пунктами (Название + Значение)

- [ ] **Step 3: Создать тестовый товар с секциями**

  Создать новый товар, добавить 2 секции через `+ Добавить секцию описания`, в каждой секции добавить 2-3 пункта с именем и значением. Сохранить.

- [ ] **Step 4: Проверить публичный API**

  ```bash
  curl http://localhost:8000/catalog/products/<ID> | python -m json.tool | grep -A 20 descriptionParameters
  ```

  Ожидаемый ответ:
  ```json
  "descriptionParameters": [
    {
      "title": "Название секции",
      "items": [
        {"name": "Напряжение", "value": "220 В"}
      ]
    }
  ]
  ```

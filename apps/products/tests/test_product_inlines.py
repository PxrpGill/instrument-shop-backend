"""Тесты инлайн-моделей ProductDescriptionBlock и ProductSpecGroup/Item."""

import pytest
from apps.products.models import (
    Product,
    ProductDescriptionBlock,
    ProductSpecGroup,
    ProductSpecItem,
    ProductStatusChoices,
)

pytestmark = pytest.mark.django_db


@pytest.fixture
def product():
    return Product.objects.create(
        name="Дрель Metabo SBE 650",
        status=ProductStatusChoices.PUBLISHED,
        price=5490,
    )


class TestProductDescriptionBlock:
    def test_create_block(self, product):
        block = ProductDescriptionBlock.objects.create(
            product=product,
            title="Общие характеристики",
            content="<p>Тип: дрель</p>",
            order=0,
        )
        assert block.pk is not None
        assert block.product == product

    def test_ordering_by_order(self, product):
        ProductDescriptionBlock.objects.create(product=product, title="B", content="", order=2)
        ProductDescriptionBlock.objects.create(product=product, title="A", content="", order=1)
        titles = list(
            ProductDescriptionBlock.objects.filter(product=product).values_list("title", flat=True)
        )
        assert titles == ["A", "B"]

    def test_content_sanitized_on_save(self, product):
        block = ProductDescriptionBlock.objects.create(
            product=product,
            title="XSS-тест",
            content='<p>Текст</p><script>alert("xss")</script>',
            order=0,
        )
        block.refresh_from_db()
        assert "<script>" not in block.content
        assert "Текст" in block.content

    def test_str(self, product):
        block = ProductDescriptionBlock.objects.create(
            product=product, title="Особенности", content="", order=0
        )
        assert "Особенности" in str(block)


class TestProductSpecGroup:
    def test_create_group_with_items(self, product):
        group = ProductSpecGroup.objects.create(
            product=product, title="Электрические параметры", order=0
        )
        item = ProductSpecItem.objects.create(
            group=group, label="Напряжение", value="220 В", order=0
        )
        assert item.group == group
        assert group.product == product

    def test_items_ordering(self, product):
        group = ProductSpecGroup.objects.create(
            product=product, title="Группа", order=0
        )
        ProductSpecItem.objects.create(group=group, label="Z", value="z", order=2)
        ProductSpecItem.objects.create(group=group, label="A", value="a", order=1)
        labels = list(
            ProductSpecItem.objects.filter(group=group).values_list("label", flat=True)
        )
        assert labels == ["A", "Z"]

    def test_str_group(self, product):
        group = ProductSpecGroup.objects.create(product=product, title="Конструкция", order=0)
        assert "Конструкция" in str(group)

    def test_str_item(self, product):
        group = ProductSpecGroup.objects.create(product=product, title="G", order=0)
        item = ProductSpecItem.objects.create(group=group, label="Вес", value="2.1 кг", order=0)
        assert "Вес" in str(item)


from apps.products.catalog_serializers import serialize_product_detail


class TestSerializeProductDetail:
    def test_description_parameters_from_blocks(self, product):
        ProductDescriptionBlock.objects.create(
            product=product, title="Общие", content="<p>Тип: дрель</p>", order=0
        )
        ProductDescriptionBlock.objects.create(
            product=product, title="Комплектация", content="<ul><li>Кейс</li></ul>", order=1
        )
        result = serialize_product_detail(product)
        assert "descriptionParameters" in result
        params = result["descriptionParameters"]
        assert len(params) == 2
        assert params[0] == {"title": "Общие", "parameters": "<p>Тип: дрель</p>"}
        assert params[1] == {"title": "Комплектация", "parameters": "<ul><li>Кейс</li></ul>"}

    def test_technical_specifications_from_groups(self, product):
        group = ProductSpecGroup.objects.create(
            product=product, title="Электрические параметры", order=0
        )
        ProductSpecItem.objects.create(group=group, label="Напряжение", value="220 В", order=0)
        ProductSpecItem.objects.create(group=group, label="Мощность", value="650 Вт", order=1)

        result = serialize_product_detail(product)
        assert "techicalSpecifications" in result
        specs = result["techicalSpecifications"]
        assert len(specs) == 1
        assert specs[0]["title"] == "Электрические параметры"
        assert specs[0]["specifications"] == [
            {"label": "Напряжение", "value": "220 В"},
            {"label": "Мощность", "value": "650 Вт"},
        ]

    def test_empty_blocks_not_in_output(self, product):
        result = serialize_product_detail(product)
        assert "descriptionParameters" not in result
        assert "techicalSpecifications" not in result

    def test_group_without_items_excluded(self, product):
        ProductSpecGroup.objects.create(product=product, title="Пустая группа", order=0)
        result = serialize_product_detail(product)
        assert "techicalSpecifications" not in result

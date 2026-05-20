"""Тесты сервисов и моделей apps.products (после перехода на shared.Image)."""

import pytest

from apps.products.models import (Category, Product, ProductImage,
                                  ProductStatusChoices)
from apps.products.services import (ProductPublicationError,
                                    ProductPublicationService)
from apps.shared.models import Image


@pytest.fixture
def image_factory():
    """Создаёт shared.Image с заглушечным source_desktop путём.

    Файл реально не загружается — для unit-тестов достаточно ImageField с
    привязанным именем. shared.Image на post_save запускает image_pipeline,
    который при отсутствии файла просто молча выйдет (нечего конвертировать).
    """

    def _factory(name: str = "img.jpg") -> Image:
        image = Image(alt_text=name)
        image.source_desktop.name = f"images/source/desktop/{name}"
        image.save()
        return image

    return _factory


@pytest.mark.django_db
class TestProductPublicationService:
    def test_get_publication_errors_no_name(self, product_factory):
        product = product_factory(name="", price=100.00)

        errors = ProductPublicationService.get_publication_errors(product)
        assert any("name" in error.lower() for error in errors)

    def test_get_publication_errors_none_price(self, category_factory, image_factory):
        category = category_factory("Test")
        product = Product.objects.create(name="No Price Product")
        product.categories.add(category)
        ProductImage.objects.create(product=product, image=image_factory())

        errors = ProductPublicationService.get_publication_errors(product)
        assert any("price" in error.lower() for error in errors)

    def test_get_publication_errors_no_image(self, product_factory, category_factory):
        category = category_factory("Test")
        product = product_factory(name="Test Product", price=100.00)
        product.categories.add(category)

        errors = ProductPublicationService.get_publication_errors(product)
        assert any("image" in error.lower() for error in errors)

    def test_get_publication_errors_no_category(self, product_factory, image_factory):
        product = product_factory(name="Test Product", price=100.00)
        ProductImage.objects.create(product=product, image=image_factory())

        errors = ProductPublicationService.get_publication_errors(product)
        assert any("category" in error.lower() for error in errors)

    def test_get_publication_errors_valid_product(
        self, product_factory, category_factory, image_factory
    ):
        category = category_factory("Test")
        product = product_factory(name="Valid Product", price=100.00)
        product.categories.add(category)
        ProductImage.objects.create(product=product, image=image_factory())

        assert ProductPublicationService.get_publication_errors(product) == []

    def test_can_publish_valid_product(
        self, product_factory, category_factory, image_factory
    ):
        category = category_factory("Test")
        product = product_factory(name="Valid", price=100.00)
        product.categories.add(category)
        ProductImage.objects.create(product=product, image=image_factory())

        assert ProductPublicationService.can_publish(product) is True

    def test_can_publish_invalid_product(self, product_factory):
        product = product_factory(name="", price=None)
        assert ProductPublicationService.can_publish(product) is False

    def test_publish_valid_product(
        self, product_factory, category_factory, image_factory
    ):
        category = category_factory("Test")
        product = product_factory(name="Publish Test", price=100.00)
        product.categories.add(category)
        ProductImage.objects.create(product=product, image=image_factory())

        published_product = ProductPublicationService.publish(product)
        assert published_product.status == ProductStatusChoices.PUBLISHED

    def test_publish_invalid_product_raises_error(self, product_factory):
        product = product_factory(name="", price=None)
        with pytest.raises(ProductPublicationError):
            ProductPublicationService.publish(product)


@pytest.mark.django_db
class TestCategoryModel:
    def test_str_returns_name(self, category_factory):
        category = category_factory("Guitars")
        assert str(category) == "Guitars"

    def test_save_generates_slug_from_name(self):
        category = Category.objects.create(name="Electric Guitars")
        assert category.slug == "electric-guitars"

    def test_save_keeps_existing_slug(self):
        category = Category.objects.create(name="Test", slug="custom-slug")
        assert category.slug == "custom-slug"


@pytest.mark.django_db
class TestProductModel:
    def test_str_returns_name(self, product_factory):
        product = product_factory(name="Test Product")
        assert str(product) == "Test Product"


@pytest.mark.django_db
class TestProductImageModel:
    def test_str_contains_product_name(self, product_factory, image_factory):
        product = product_factory(name="Test Product")
        pi = ProductImage.objects.create(product=product, image=image_factory())
        assert "Test Product" in str(pi)

    def test_save_sets_primary_and_unsets_others(self, product_factory, image_factory):
        product = product_factory(name="Test Product")
        image1 = ProductImage.objects.create(
            product=product, image=image_factory("a.jpg"), is_primary=True
        )
        image2 = ProductImage.objects.create(
            product=product, image=image_factory("b.jpg"), is_primary=False
        )

        image2.is_primary = True
        image2.save()

        image1.refresh_from_db()
        image2.refresh_from_db()
        assert image1.is_primary is False
        assert image2.is_primary is True

"""
Tests for products services.
"""
import pytest

from apps.products.models import Category, Product, ProductImage, ProductStatusChoices
from apps.products.services import ProductPublicationError, ProductPublicationService


@pytest.mark.django_db
class TestProductPublicationService:
    """Tests for ProductPublicationService."""

    def test_get_publication_errors_no_name(self, product_factory):
        """Test publication errors when name is missing."""
        product = product_factory(name="", price=100.00)  # Empty name
        
        errors = ProductPublicationService.get_publication_errors(product)        
        assert len(errors) > 0
        assert any("name" in error.lower() for error in errors)

    def test_get_publication_errors_none_price(self, product_factory, category_factory):
        """Test publication errors when price is None."""
        category = category_factory("Test")
        # Create product with price=None directly via model
        product = Product.objects.create(name="No Price Product")
        product.categories.add(category)
        ProductImage.objects.create(product=product, image="test.jpg")
        
        errors = ProductPublicationService.get_publication_errors(product)        
        assert len(errors) > 0
        assert any("price" in error.lower() for error in errors)

    def test_get_publication_errors_no_price(self, product_factory, category_factory):
        """Test publication errors when price is None."""
        category = category_factory("Test")
        # Create product with price=None directly via model
        product = Product.objects.create(name="No Price Product")
        product.categories.add(category)
        ProductImage.objects.create(product=product, image="test.jpg")
        
        errors = ProductPublicationService.get_publication_errors(product)        
        assert len(errors) > 0
        assert any("price" in error.lower() for error in errors)

    def test_get_publication_errors_no_image(self, product_factory, category_factory):
        """Test publication errors when no image."""
        category = category_factory("Test")
        product = product_factory(name="Test Product", price=100.00)
        product.categories.add(category)
        # No image added
        
        errors = ProductPublicationService.get_publication_errors(product)
        
        assert len(errors) > 0
        assert any("image" in error.lower() for error in errors)

    def test_get_publication_errors_no_category(self, product_factory):
        """Test publication errors when no category."""
        product = product_factory(name="Test Product", price=100.00)
        ProductImage.objects.create(product=product, image="test.jpg")
        # No category added
        
        errors = ProductPublicationService.get_publication_errors(product)
        
        assert len(errors) > 0
        assert any("category" in error.lower() for error in errors)

    def test_get_publication_errors_valid_product(self, product_factory, category_factory):
        """Test no errors for valid product."""
        category = category_factory("Test")
        product = product_factory(name="Valid Product", price=100.00)
        product.categories.add(category)
        ProductImage.objects.create(product=product, image="test.jpg")
        
        errors = ProductPublicationService.get_publication_errors(product)
        
        assert errors == []

    def test_can_publish_valid_product(self, product_factory, category_factory):
        """Test can_publish returns True for valid product."""
        category = category_factory("Test")
        product = product_factory(name="Valid Product", price=100.00)
        product.categories.add(category)
        ProductImage.objects.create(product=product, image="test.jpg")
        
        result = ProductPublicationService.can_publish(product)
        
        assert result is True

    def test_can_publish_invalid_product(self, product_factory):
        """Test can_publish returns False for invalid product."""
        product = product_factory(name="", price=None)  # Invalid
        
        result = ProductPublicationService.can_publish(product)
        
        assert result is False

    def test_publish_valid_product(self, product_factory, category_factory):
        """Test publishing a valid product."""
        category = category_factory("Test")
        product = product_factory(name="Publish Test", price=100.00)
        product.categories.add(category)
        ProductImage.objects.create(product=product, image="test.jpg")
        
        assert product.status == ProductStatusChoices.DRAFT
        
        published_product = ProductPublicationService.publish(product)
        
        assert published_product.status == ProductStatusChoices.PUBLISHED

    def test_publish_invalid_product_raises_error(self, product_factory):
        """Test publishing invalid product raises ProductPublicationError."""
        product = product_factory(name="", price=None)  # Invalid
        
        with pytest.raises(ProductPublicationError):
            ProductPublicationService.publish(product)


@pytest.mark.django_db
class TestCategoryModel:
    """Tests for Category model edge cases."""

    def test_str_returns_name(self, category_factory):
        """Test Category __str__ returns name."""
        category = category_factory("Guitars")
        
        assert str(category) == "Guitars"

    def test_save_generates_slug_from_name(self, category_factory):
        """Test that save generates slug if not provided."""
        category = Category.objects.create(name="Electric Guitars")
        
        assert category.slug == "electric-guitars"

    def test_save_keeps_existing_slug(self, category_factory):
        """Test that save doesn't overwrite existing slug."""
        category = Category.objects.create(name="Test", slug="custom-slug")
        
        assert category.slug == "custom-slug"


@pytest.mark.django_db
class TestProductModel:
    """Tests for Product model edge cases."""

    def test_str_returns_name(self, product_factory):
        """Test Product __str__ returns name."""
        product = product_factory(name="Test Product")
        
        assert str(product) == "Test Product"


@pytest.mark.django_db
class TestProductImageModel:
    """Tests for ProductImage model edge cases."""

    def test_str_format(self, product_factory):
        """Test ProductImage __str__ format."""
        product = product_factory(name="Test Product")
        image = ProductImage.objects.create(
            product=product, image="test.jpg", alt_text="Test"
        )
        
        result = str(image)
        assert "Test Product" in result
        assert "test.jpg" in result

    def test_save_sets_primary_and_unsets_others(self, product_factory):
        """Test that setting is_primary=True unsets other images."""
        product = product_factory(name="Test Product")
        image1 = ProductImage.objects.create(
            product=product, image="test1.jpg", is_primary=True
        )
        image2 = ProductImage.objects.create(
            product=product, image="test2.jpg", is_primary=False
        )
        
        # Set image2 as primary
        image2.is_primary = True
        image2.save()
        
        image1.refresh_from_db()
        image2.refresh_from_db()
        
        assert image1.is_primary is False
        assert image2.is_primary is True

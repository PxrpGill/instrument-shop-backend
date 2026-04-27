import logging
from dataclasses import dataclass

from ninja.errors import HttpError
from rest_framework import status

from .models import Product, ProductStatusChoices

logger = logging.getLogger(__name__)


@dataclass
class PublicationRule:
    """Represents a single publication rule check."""

    field: str
    message: str


class ProductPublicationError(HttpError):
    """Exception raised when a product cannot be published."""

    def __init__(self, errors: list[str]) -> None:
        self.errors = errors
        message = "; ".join(errors)
        super().__init__(status_code=status.HTTP_400_BAD_REQUEST, message=message)


class ProductPublicationService:
    """
    Service for handling product publication logic.

    Encapsulates all rules for when a product can be published.
    """

    REQUIRED_FIELDS = ["name", "price"]

    @classmethod
    def get_publication_errors(cls, product: Product) -> list[str]:
        """
        Get list of publication rule violations for a product.

        Returns empty list if product is ready for publication.
        """
        errors: list[str] = []

        for field in cls.REQUIRED_FIELDS:
            value = getattr(product, field, None)
            # Check if value is None (not set)
            if value is None:
                errors.append(f"Field '{field}' is required for publication")
            # For string fields, also check for empty string
            elif isinstance(value, str) and value.strip() == "":
                errors.append(f"Field '{field}' is required for publication")

        if not product.images.exists():
            errors.append("At least one image is required for publication")

        if not product.categories.exists():
            errors.append("At least one category is required for publication")

        return errors

    @classmethod
    def can_publish(cls, product: Product) -> bool:
        """Check if a product can be published."""
        return len(cls.get_publication_errors(product)) == 0

    @classmethod
    def publish(cls, product: Product) -> Product:
        """
        Publish a product if it meets all requirements.

        Raises ProductPublicationError if product cannot be published.
        """
        errors = cls.get_publication_errors(product)
        if errors:
            logger.warning(f"Product {product.id} failed publication: {errors}")
            raise ProductPublicationError(errors)

        product.status = ProductStatusChoices.PUBLISHED
        product.save()
        logger.info(f"Product {product.id} published successfully")
        return product

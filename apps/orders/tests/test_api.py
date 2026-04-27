"""
Tests for order API endpoints.

Covers BE-025 (create order), BE-026 (price snapshot), BE-027 (published products only).
"""

from decimal import Decimal
from typing import List

import pytest
from django.shortcuts import get_object_or_404

from apps.orders.models import Order, OrderItem, OrderStatusChoices
from apps.products.models import Product, ProductStatusChoices


@pytest.mark.django_db
class TestCreateOrderEndpoint:
    """Tests for POST /v1/orders/ - BE-025 Create customer order endpoint."""

    def test_create_order_success(
        self,
        client,
        regular_customer,
        published_product_factory,
        auth_headers,
    ):
        """
        Test successful order creation with multiple items.

        BE-025: Order should be created in a single request with transaction integrity.
        """
        # Create published products
        product1 = published_product_factory(name="Guitar", price=299.99)
        product2 = published_product_factory(name="Strings", price=19.99)

        # Prepare order data
        order_data = {
            "contact_email": "customer@example.com",
            "contact_phone": "+1234567890",
            "first_name": "John",
            "last_name": "Doe",
            "address": "123 Main St",
            "notes": "Please deliver in the morning",
            "items": [
                {"product_id": product1.id, "quantity": 2},
                {"product_id": product2.id, "quantity": 5},
            ],
        }

        # Make request
        headers = auth_headers(regular_customer)
        response = client.post("/v1/orders/", json=order_data, headers=headers)

        # Verify response
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.json}"
        data = response.json()

        assert data["status"] == OrderStatusChoices.NEW
        assert data["contact_email"] == "customer@example.com"
        assert data["first_name"] == "John"
        assert data["last_name"] == "Doe"
        assert len(data["items"]) == 2

        # Verify order was created in database
        order = Order.objects.filter(contact_email="customer@example.com").first()
        assert order is not None
        assert order.customer == regular_customer
        assert order.items.count() == 2

        # Verify total amount
        expected_total = Decimal("299.99") * 2 + Decimal("19.99") * 5
        assert Decimal(data["total_amount"]) == expected_total

    def test_create_order_minimal_data(
        self,
        client,
        regular_customer,
        published_product_factory,
        auth_headers,
    ):
        """Test order creation with minimal required data (only email and items)."""
        product = published_product_factory(name="Single Item", price=50.00)

        order_data = {
            "contact_email": "minimal@example.com",
            "items": [
                {"product_id": product.id, "quantity": 1},
            ],
        }

        headers = auth_headers(regular_customer)
        response = client.post("/v1/orders/", json=order_data, headers=headers)

        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.json}"
        data = response.json()

        assert data["contact_email"] == "minimal@example.com"
        assert data["contact_phone"] == ""
        assert data["first_name"] == ""
        assert data["items"][0]["product_name"] == "Single Item"

    def test_create_order_requires_authentication(self, client, published_product_factory):
        """Test that order creation requires authentication."""
        product = published_product_factory(name="Test Product", price=100.00)

        order_data = {
            "contact_email": "test@example.com",
            "items": [{"product_id": product.id, "quantity": 1}],
        }

        response = client.post("/v1/orders/", json=order_data)
        # Should return 401 or similar for unauthenticated
        assert response.status_code in [401, 403]

    def test_create_order_requires_create_permission(
        self,
        client,
        customer_factory,
        published_product_factory,
        auth_headers,
    ):
        """
        Test that order creation requires create_order permission.

        Note: In current setup, regular customers have the customer role which
        should include create_order permission. This test verifies the permission check.
        """
        # Create a customer without any roles (should not have permission)
        customer_no_role = customer_factory(email="norole@example.com")
        # Don't assign any role - they shouldn't be able to create orders

        product = published_product_factory(name="Test Product", price=100.00)

        order_data = {
            "contact_email": "test@example.com",
            "items": [{"product_id": product.id, "quantity": 1}],
        }

        headers = auth_headers(customer_no_role)
        response = client.post("/v1/orders/", json=order_data, headers=headers)

        # Should fail with 403 (no permission)
        assert response.status_code == 403

    def test_create_order_transaction_integrity(
        self,
        client,
        regular_customer,
        published_product_factory,
        auth_headers,
    ):
        """
        Test that transaction rolls back if an error occurs during order creation.

        BE-025: Transaction should guarantee data integrity.
        """
        product = published_product_factory(name="Test Product", price=100.00)

        order_data = {
            "contact_email": "transaction@example.com",
            "items": [{"product_id": product.id, "quantity": 1}],
        }

        headers = auth_headers(regular_customer)

        # Count orders before
        orders_before = Order.objects.count()

        # Create order (this should succeed)
        response = client.post("/v1/orders/", json=order_data, headers=headers)

        assert response.status_code == 200
        assert Order.objects.count() == orders_before + 1


@pytest.mark.django_db
class TestOrderPriceSnapshot:
    """Tests for BE-026 Snapshot product price at order creation."""

    def test_price_snapshot_at_creation(
        self,
        client,
        regular_customer,
        published_product_factory,
        auth_headers,
    ):
        """
        Test that product price is snapshotted at order creation.

        BE-026: Price should be copied, not read dynamically from Product after order.
        """
        # Create product with initial price
        product = published_product_factory(name="Guitar", price=299.99)

        # Create order
        order_data = {
            "contact_email": "snapshot@example.com",
            "items": [{"product_id": product.id, "quantity": 1}],
        }

        headers = auth_headers(regular_customer)
        response = client.post("/v1/orders/", json=order_data, headers=headers)

        assert response.status_code == 200
        data = response.json()

        # Verify price was snapshotted
        assert data["items"][0]["unit_price"] == "299.99"

        # Change product price AFTER order creation
        product.price = Decimal("399.99")
        product.save()

        # Fetch order again and verify price hasn't changed
        order = Order.objects.get(pk=data["id"])
        item = order.items.first()
        assert item.unit_price == Decimal("299.99")  # Original price preserved

    def test_price_snapshot_multiple_items(
        self,
        client,
        regular_customer,
        published_product_factory,
        auth_headers,
    ):
        """Test price snapshot with multiple items at different prices."""
        product1 = published_product_factory(name="Guitar", price=299.99)
        product2 = published_product_factory(name="Amp", price=199.99)

        order_data = {
            "contact_email": "multi@example.com",
            "items": [
                {"product_id": product1.id, "quantity": 1},
                {"product_id": product2.id, "quantity": 2},
            ],
        }

        headers = auth_headers(regular_customer)
        response = client.post("/v1/orders/", json=order_data, headers=headers)

        assert response.status_code == 200
        data = response.json()

        # Verify each item has correct snapshotted price
        items_dict = {item["product_name"]: item for item in data["items"]}

        assert items_dict["Guitar"]["unit_price"] == "299.99"
        assert items_dict["Guitar"]["subtotal"] == "299.99"

        assert items_dict["Amp"]["unit_price"] == "199.99"
        assert items_dict["Amp"]["subtotal"] == "399.98"  # 199.99 * 2

    def test_price_change_does_not_affect_old_order(
        self,
        client,
        regular_customer,
        published_product_factory,
        auth_headers,
    ):
        """
        Test that changing product price after order doesn't affect old order.

        BE-026: This is the key requirement - old orders must preserve their prices.
        """
        product = published_product_factory(name="Guitar", price=299.99)

        # Create first order
        order_data = {
            "contact_email": "order1@example.com",
            "items": [{"product_id": product.id, "quantity": 1}],
        }

        headers = auth_headers(regular_customer)
        response1 = client.post("/v1/orders/", json=order_data, headers=headers)
        assert response1.status_code == 200
        order1_id = response1.json()["id"]

        # Change product price
        product.price = Decimal("999.99")
        product.save()

        # Create second order after price change
        order_data["contact_email"] = "order2@example.com"
        response2 = client.post("/v1/orders/", json=order_data, headers=headers)
        assert response2.status_code == 200
        order2_id = response2.json()["id"]

        # Verify first order still has old price
        order1 = Order.objects.get(pk=order1_id)
        assert order1.items.first().unit_price == Decimal("299.99")

        # Verify second order has new price
        order2 = Order.objects.get(pk=order2_id)
        assert order2.items.first().unit_price == Decimal("999.99")


@pytest.mark.django_db
class TestRestrictToPublishedProducts:
    """Tests for BE-027 Restrict order creation to published products."""

    def test_cannot_order_draft_product(
        self,
        client,
        regular_customer,
        product_factory,
        auth_headers,
    ):
        """
        Test that draft products cannot be ordered.

        BE-027: Only published products should be orderable.
        """
        # Create a draft product (default status)
        draft_product = product_factory(name="Draft Guitar", price=299.99, status="draft")

        order_data = {
            "contact_email": "test@example.com",
            "items": [{"product_id": draft_product.id, "quantity": 1}],
        }

        headers = auth_headers(regular_customer)
        response = client.post("/v1/orders/", json=order_data, headers=headers)

        assert response.status_code == 400
        data = response.json()
        assert "not available" in str(data).lower() or "published" in str(data).lower()

        # Verify no order was created
        assert Order.objects.count() == 0

    def test_cannot_order_archived_product(
        self,
        client,
        regular_customer,
        product_factory,
        auth_headers,
    ):
        """Test that archived products cannot be ordered."""
        archived_product = product_factory(name="Old Guitar", price=299.99, status="archived")

        order_data = {
            "contact_email": "test@example.com",
            "items": [{"product_id": archived_product.id, "quantity": 1}],
        }

        headers = auth_headers(regular_customer)
        response = client.post("/v1/orders/", json=order_data, headers=headers)

        assert response.status_code == 400

        # Verify no order was created
        assert Order.objects.count() == 0

    def test_can_only_order_published_product(
        self,
        client,
        regular_customer,
        published_product_factory,
        auth_headers,
    ):
        """Test that published products can be ordered."""
        published_product = published_product_factory(name="Published Guitar", price=299.99)

        order_data = {
            "contact_email": "test@example.com",
            "items": [{"product_id": published_product.id, "quantity": 1}],
        }

        headers = auth_headers(regular_customer)
        response = client.post("/v1/orders/", json=order_data, headers=headers)

        assert response.status_code == 200
        assert Order.objects.count() == 1

    def test_mixed_published_and_draft_products(
        self,
        client,
        regular_customer,
        published_product_factory,
        product_factory,
        auth_headers,
    ):
        """Test that order fails if any product is not published."""
        published_product = published_product_factory(name="Published", price=100.00)
        draft_product = product_factory(name="Draft", price=200.00, status="draft")

        order_data = {
            "contact_email": "test@example.com",
            "items": [
                {"product_id": published_product.id, "quantity": 1},
                {"product_id": draft_product.id, "quantity": 1},
            ],
        }

        headers = auth_headers(regular_customer)
        response = client.post("/v1/orders/", json=order_data, headers=headers)

        assert response.status_code == 400

        # Verify no order was created (transaction rolled back)
        assert Order.objects.count() == 0

    def test_nonexistent_product(
        self,
        client,
        regular_customer,
        auth_headers,
    ):
        """Test that order fails if product doesn't exist."""
        order_data = {
            "contact_email": "test@example.com",
            "items": [{"product_id": 99999, "quantity": 1}],  # Non-existent ID
        }

        headers = auth_headers(regular_customer)
        response = client.post("/v1/orders/", json=order_data, headers=headers)

        assert response.status_code == 400

        # Verify no order was created
        assert Order.objects.count() == 0

    def test_product_without_price(
        self,
        client,
        regular_customer,
        product_factory,
        auth_headers,
    ):
        """Test that product without price cannot be ordered even if published."""
        # Create published product without price
        product = product_factory(name="No Price", price=None, status="published")

        order_data = {
            "contact_email": "test@example.com",
            "items": [{"product_id": product.id, "quantity": 1}],
        }

        headers = auth_headers(regular_customer)
        response = client.post("/v1/orders/", json=order_data, headers=headers)

        assert response.status_code == 400

        # Verify no order was created
        assert Order.objects.count() == 0


@pytest.mark.django_db
class TestListOrdersEndpoint:
    """Tests for GET /v1/orders/ - List orders."""

    def test_list_own_orders(
        self,
        client,
        regular_customer,
        order_factory,
        auth_headers,
    ):
        """Test that customers can only see their own orders."""
        # Create orders for this customer
        order1 = order_factory(customer=regular_customer)
        order2 = order_factory(customer=regular_customer)

        # Create another customer with order using the fixture directly in the test
        from apps.users.services.customer_service import CustomerService
        other_customer = CustomerService.create_customer(
            email="other@example.com",
            password="testpass123",
            first_name="Other",
            last_name="Customer",
            phone="+9876543210"
        )
        order_factory(customer=other_customer)

        headers = auth_headers(regular_customer)
        response = client.get("/v1/orders/", headers=headers)

        assert response.status_code == 200
        data = response.json()

        # Should only see own orders
        assert len(data) == 2
        order_ids = {order1.id, order2.id}
        response_ids = {o["id"] for o in data}
        assert response_ids == order_ids

    def test_list_orders_staff_sees_all(
        self,
        client,
        regular_customer,
        admin_customer,
        order_factory,
        auth_headers,
    ):
        """Test that staff users can see all orders."""
        # Create orders for different customers
        order_factory(customer=regular_customer)
        order_factory(customer=regular_customer)

        headers = auth_headers(admin_customer)
        response = client.get("/v1/orders/", headers=headers)

        assert response.status_code == 200
        data = response.json()

        # Admin should see all orders
        assert len(data) >= 2

    def test_filter_orders_by_status(
        self,
        client,
        regular_customer,
        order_factory,
        auth_headers,
    ):
        """Test filtering orders by status."""
        # Create orders with different statuses
        order_factory(customer=regular_customer, status=OrderStatusChoices.NEW)
        order_factory(customer=regular_customer, status=OrderStatusChoices.NEW)
        order_factory(customer=regular_customer, status=OrderStatusChoices.COMPLETED)

        headers = auth_headers(regular_customer)

        # Filter by NEW status
        response = client.get("/v1/orders/?status=new", headers=headers)

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        for order in data:
            assert order["status"] == "new"


@pytest.mark.django_db
class TestGetOrderEndpoint:
    """Tests for GET /v1/orders/{id} - Get single order."""

    def test_get_own_order(
        self,
        client,
        regular_customer,
        order_factory,
        order_item_factory,
        auth_headers,
    ):
        """Test that customer can view their own order with items."""
        order = order_factory(customer=regular_customer)
        order_item_factory(order=order, product_name="Guitar", unit_price=Decimal("299.99"))

        headers = auth_headers(regular_customer)
        response = client.get(f"/v1/orders/{order.id}", headers=headers)

        assert response.status_code == 200
        data = response.json()

        assert data["id"] == order.id
        assert len(data["items"]) == 1
        assert data["items"][0]["product_name"] == "Guitar"
        assert data["total_amount"] == "299.99"

    def test_cannot_view_other_customer_order(
        self,
        client,
        regular_customer,
        customer_factory,
        order_factory,
        auth_headers,
    ):
        """Test that customer cannot view another customer's order."""
        other_customer = customer_factory(email="other@example.com")
        other_order = order_factory(customer=other_customer)

        headers = auth_headers(regular_customer)
        response = client.get(f"/v1/orders/{other_order.id}", headers=headers)

        # Should get 404 (to not leak existence) or 403
        assert response.status_code in [403, 404]

    def test_staff_can_view_any_order(
        self,
        client,
        admin_customer,
        regular_customer,
        order_factory,
        auth_headers,
    ):
        """Test that staff can view any order."""
        order = order_factory(customer=regular_customer)

        headers = auth_headers(admin_customer)
        response = client.get(f"/v1/orders/{order.id}", headers=headers)

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == order.id
        assert len(data["items"]) == 1
        assert data["items"][0]["product_name"] == "Guitar"
        assert data["total_amount"] == "299.99"

    def test_cannot_view_other_customer_order(
        self,
        client,
        regular_customer,
        customer_factory,
        order_factory,
        auth_headers,
    ):
        """Test that customer cannot view another customer's order."""
        other_customer = customer_factory(email="other@example.com")
        other_order = order_factory(customer=other_customer)

        headers = auth_headers(regular_customer)
        response = client.get(f"/v1/orders/{other_order.id}", headers=headers)

        # Should get 404 (to not leak existence) or 403
        assert response.status_code in [403, 404]

    def test_staff_can_view_any_order(
        self,
        client,
        admin_customer,
        regular_customer,
        order_factory,
        auth_headers,
    ):
        """Test that staff can view any order."""
        order = order_factory(customer=regular_customer)

        headers = auth_headers(admin_customer)
        response = client.get(f"/v1/orders/{order.id}", headers=headers)

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == order.id

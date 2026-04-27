"""
Order controllers - API endpoints for order operations.

This module defines the API endpoints for creating and managing orders.
Controllers should be thin - they validate input, delegate to services, and return responses.
"""

from typing import List, Optional

from ninja import Router

from apps.orders.models import Order, OrderStatusChoices
from apps.orders.schemas import (
    OrderCreateSchema,
    OrderListResponseSchema,
    OrderResponseSchema,
    OrderStatusUpdateSchema,
)
from apps.orders.services import OrderCreationError, OrderService
from apps.users.api.controllers import get_customer_from_request
from apps.users.constants import Permission, RoleName
from core.auth.permissions import HasPermission, HasRoleMixin

# Create router for orders
router = Router(tags=["Orders"])


@router.post("", response=OrderResponseSchema)
def create_order(request, payload: OrderCreateSchema):
    """
    Create a new order.

    Creates an order with items in a single transaction.
    Requires create_order permission (any authenticated customer can order).

    The order will be created with status 'new' and items will have
    product name and price snapshotted at the time of order creation.

    Only published products with prices can be ordered.
    """
    customer = get_customer_from_request(request)
    HasRoleMixin.require_permission(customer, Permission.CREATE_ORDER)

    try:
        order = OrderService.create_order(customer, payload)
        return order
    except OrderCreationError as e:
        # Return 400 with validation errors
        from ninja.errors import HttpError

        raise HttpError(400, str(e.errors))


@router.get("", response=List[OrderListResponseSchema])
def list_orders(
    request,
    status: Optional[str] = None,
):
    """
    List orders (staff only).

    Staff users (admin/catalog_manager) can see all orders.
    Customers and guests are denied access.

    Filter by status using query parameter: ?status=new
    """
    customer = get_customer_from_request(request)

    # Only staff can list orders (BE-028: customer or guest access should not be granted)
    has_permission = customer.has_role(RoleName.ADMIN) or customer.has_role(
        RoleName.CATALOG_MANAGER
    )
    if not has_permission:
        from ninja.errors import HttpError

        raise HttpError(403, "Access denied. Staff only.")

    # Staff can see all orders
    queryset = Order.objects.select_related("customer").prefetch_related("items").all()

    # Filter by status if provided
    if status:
        queryset = queryset.filter(status=status)

    return queryset.order_by("-created_at")


@router.get("/{int:order_id}", response=OrderResponseSchema)
def get_order(request, order_id: int):
    """
    Get a single order by ID.

    Customers can only view their own orders.
    Staff users (with view_order permission) can view any order.
    """
    customer = get_customer_from_request(request)

    # Try to get the order
    order = (
        Order.objects.select_related("customer")
        .prefetch_related("items")
        .filter(pk=order_id)
        .first()
    )

    if not order:
        from django.shortcuts import get_object_or_404

        get_object_or_404(Order, pk=order_id)  # This will raise 404

    # Check permissions
    if order.customer != customer:
        # Not the order owner - check if staff can view
        # Staff check: user must have view_order permission AND not be a regular customer
        # Admin always can, catalog_manager can (they have view_customer permission)
        is_staff = customer.has_role(RoleName.ADMIN) or customer.has_role(
            RoleName.CATALOG_MANAGER
        )
        if not is_staff:
            from ninja.errors import HttpError

            raise HttpError(404, "Order not found")

    return order


@router.post("/{int:order_id}/cancel", response=OrderResponseSchema)
def cancel_order(request, order_id: int):
    """
    Cancel an order.

    Customers can cancel their own orders if they are in 'new' or 'processing' status.
    Staff users (with cancel_order permission) can cancel any order.
    """
    customer = get_customer_from_request(request)

    order = (
        Order.objects.select_related("customer")
        .prefetch_related("items")
        .filter(pk=order_id)
        .first()
    )

    if not order:
        from django.shortcuts import get_object_or_404

        get_object_or_404(Order, pk=order_id)

    # Check if customer can cancel this order
    if order.customer != customer:
        # Not the order owner - check if staff can cancel
        HasRoleMixin.require_permission(customer, Permission.CANCEL_ORDER)
    else:
        # Customer cancelling their own order
        # Check if order can be cancelled
        if not OrderService.can_cancel_order(order):
            from ninja.errors import HttpError

            raise HttpError(400, f"Order cannot be cancelled in status: {order.status}")

    # Cancel the order
    order.status = OrderStatusChoices.CANCELLED
    order.save(update_fields=["status", "updated_at"])

    return order


# Staff-only endpoints for managing order status


@router.put("/{int:order_id}/status", response=OrderResponseSchema)
def update_order_status(request, order_id: int, payload: OrderStatusUpdateSchema):
    """
    Update order status.

    Requires manage_order_status permission (staff only).
    Allows setting order status to: processing, confirmed, cancelled, completed.
    """
    customer = get_customer_from_request(request)
    HasRoleMixin.require_permission(customer, Permission.MANAGE_ORDER_STATUS)

    order = (
        Order.objects.select_related("customer")
        .prefetch_related("items")
        .filter(pk=order_id)
        .first()
    )

    if not order:
        from django.shortcuts import get_object_or_404

        get_object_or_404(Order, pk=order_id)

    # Update status
    order.status = payload.status
    order.save(update_fields=["status", "updated_at"])

    return order

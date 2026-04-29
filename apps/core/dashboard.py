"""
Dashboard callback for Unfold admin interface.

Provides statistics and KPIs for the admin dashboard.
"""
from django.db.models import Count, Sum, F, Q
from django.db.models.functions import TruncMonth
from django.utils import timezone
from datetime import timedelta

from apps.orders.models import Order, OrderItem, OrderStatusChoices
from apps.users.models import Customer
from apps.products.models import Product, ProductStatusChoices, ProductAvailabilityChoices


def dashboard_callback(request, context):
    """
    Prepare dashboard statistics for admin index page.
    
    Args:
        request: HttpRequest object
        context: Existing template context
        
    Returns:
        Updated context dictionary with dashboard statistics
    """
    # Time ranges
    now = timezone.now()
    today = now.date()
    week_ago = today - timedelta(days=7)
    month_ago = today - timedelta(days=30)

    # ====================
    # Order Statistics
    # ====================
    orders = Order.objects.all()
    total_orders = orders.count()
    new_orders = orders.filter(status=OrderStatusChoices.NEW).count()

    # Revenue calculation - use database aggregation for performance
    # Sum of all order items for confirmed/completed orders
    total_revenue = (
        OrderItem.objects.filter(
            order__status__in=[OrderStatusChoices.CONFIRMED, OrderStatusChoices.COMPLETED]
        ).aggregate(
            total=Sum(F('quantity') * F('unit_price'))
        )['total'] or 0
    )

    # Orders by status (for breakdown chart)
    orders_by_status = orders.values('status').annotate(count=Count('id')).order_by('status')

    # Recent orders (last 10) - optimize with select_related
    recent_orders = orders.select_related('customer').prefetch_related('items')[:10]

    # Orders awaiting processing (new status) - action required
    awaiting_orders = orders.filter(
        status=OrderStatusChoices.NEW
    ).select_related('customer').prefetch_related('items')[:5]

    # ====================
    # Customer Statistics
    # ====================
    total_customers = Customer.objects.filter(is_active=True).count()
    new_customers_week = Customer.objects.filter(
        created_at__date__gte=week_ago,
        is_active=True
    ).count()
    recent_customers = Customer.objects.filter(
        is_active=True
    ).order_by('-created_at')[:5]

    # ====================
    # Product Statistics
    # ====================
    products = Product.objects.all()
    total_products = products.count()
    published_products = products.filter(status=ProductStatusChoices.PUBLISHED).count()

    # Products by status
    products_by_status = products.values('status').annotate(count=Count('id')).order_by('status')

    # Products by availability
    products_by_availability = products.values('availability').annotate(
        count=Count('id')
    ).order_by('availability')

    # Products without images (potential issues)
    products_without_images = products.filter(images__isnull=True).distinct().count()

    # Products without categories
    products_without_categories = products.filter(categories__isnull=True).distinct().count()

    # ====================
    # Additional Metrics
    # ====================
    # Orders this month
    orders_this_month = orders.filter(created_at__date__gte=month_ago).count()

    # Revenue this month
    revenue_this_month = (
        OrderItem.objects.filter(
            order__status__in=[OrderStatusChoices.CONFIRMED, OrderStatusChoices.COMPLETED],
            order__created_at__date__gte=month_ago
        ).aggregate(
            total=Sum(F('quantity') * F('unit_price'))
        )['total'] or 0
    )

    # ====================
    # Chart Data: Monthly Sales Revenue
    # ====================
    monthly_sales = (
        Order.objects
        .filter(status__in=[OrderStatusChoices.CONFIRMED, OrderStatusChoices.COMPLETED])
        .annotate(month=TruncMonth('created_at'))
        .values('month')
        .annotate(
            total=Sum(F('items__quantity') * F('items__unit_price'))
        )
        .order_by('month')
    )

    monthly_sales_labels = [item['month'].strftime('%B %Y') for item in monthly_sales]
    monthly_sales_data = [float(item['total'] or 0) for item in monthly_sales]

    # ====================
    # Chart Data: Sales by Category
    # ====================
    sales_by_category = (
        OrderItem.objects
        .filter(order__status__in=[OrderStatusChoices.CONFIRMED, OrderStatusChoices.COMPLETED])
        .values('product__categories__name')
        .annotate(
            total=Sum(F('quantity') * F('unit_price')),
            count=Count('id')
        )
        .order_by('-total')[:10]
    )

    category_labels = [item['product__categories__name'] or 'Без категории'
                       for item in sales_by_category]
    category_data = [float(item['total'] or 0) for item in sales_by_category]

    # ====================
    # Chart Data: Order Status Distribution
    # ====================
    status_distribution = orders.values('status').annotate(count=Count('id'))

    status_labels = []
    status_data = []
    status_colors = {
        'new': 'rgb(234, 179, 8)',
        'processing': 'rgb(59, 130, 246)',
        'confirmed': 'rgb(34, 197, 94)',
        'completed': 'rgb(107, 114, 128)',
        'cancelled': 'rgb(239, 68, 68)',
    }

    for item in status_distribution:
        status_labels.append(dict(OrderStatusChoices.choices)[item['status']])
        status_data.append(item['count'])

    colors = [status_colors.get(item['status'], 'rgb(156, 163, 175)')
              for item in status_distribution]

    # Update context with all statistics
    context.update({
        # KPI Cards
        'total_orders': total_orders,
        'new_orders': new_orders,
        'total_revenue': total_revenue,
        'total_customers': total_customers,
        'published_products': published_products,
        'total_products': total_products,

        # Breakdowns
        'orders_by_status': orders_by_status,
        'products_by_status': products_by_status,
        'products_by_availability': products_by_availability,

        # Lists (actionable items)
        'recent_orders': recent_orders,
        'awaiting_orders': awaiting_orders,
        'recent_customers': recent_customers,

        # Additional metrics
        'new_customers_week': new_customers_week,
        'products_without_images': products_without_images,
        'products_without_categories': products_without_categories,
        'orders_this_month': orders_this_month,
        'revenue_this_month': revenue_this_month,

        # Chart Data: Monthly Sales
        'monthly_sales_labels': monthly_sales_labels,
        'monthly_sales_data': monthly_sales_data,

        # Chart Data: Sales by Category
        'category_labels': category_labels,
        'category_data': category_data,

        # Chart Data: Order Status Distribution
        'status_labels': status_labels,
        'status_data': status_data,
        'status_colors': colors,
    })

    return context

# Task 14: Admin Dashboard with Statistics

## Overview
Create a custom admin dashboard for Unfold that displays key business metrics and statistics. The dashboard will provide a quick overview of shop activity including orders, users, and products.

## Current State Analysis
- **Unfold admin** is installed and configured (`django-unfold>=0.90.0`)
- **Custom admin templates**: Not yet created (no `templates/` directory)
- **Dashboard callback**: Not configured in `UNFOLD` settings
- **Data available**:
  - `Order` model: status, created_at, items with unit_price/quantity
  - `Customer` model: created_at, roles
  - `Product` model: status, availability, categories

## Dashboard Metrics Design

### 1. KPI Cards (Top Row)
**Key Performance Indicators** - most important numbers at a glance:

| Metric | Description | Query |
|--------|-------------|-------|
| `total_orders` | Total orders count | `Order.objects.count()` |
| `new_orders` | Orders with "new" status (awaiting processing) | `Order.objects.filter(status='new').count()` |
| `total_revenue` | Revenue from confirmed/completed orders | Sum of `unit_price * quantity` for non-cancelled orders |
| `total_customers` | Registered customers | `Customer.objects.filter(is_active=True).count()` |
| `published_products` | Products available in catalog | `Product.objects.filter(status='published').count()` |

### 2. Order Status Breakdown
**Visual distribution** of order statuses (for quick action identification):

```
new: X orders
processing: X orders
confirmed: X orders
cancelled: X orders
completed: X orders
```

### 3. Recent Activity (Tables/Lists)
**Actionable items** for the admin:

- **Recent Orders** (last 5-10): ID, customer email, status, total, date
- **Orders Awaiting Processing** (status="new"): ID, customer, date - with link to process
- **New Customers** (last 5 registered): email, date

### 4. Product Overview
**Catalog health metrics**:

- Total products by status (draft/published/archived)
- Products by availability (in_stock/out_of_stock/on_request)
- Products without images (potential issues)
- Products without categories

## Technical Implementation Plan

### Step 1: Configure Template Directory
**File**: `instrument_shop/settings.py`

Ensure `TEMPLATES` setting has proper `DIRS`:
```python
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / "templates"],  # Add this if not present
        'APP_DIRS': True,
        ...
    }
]
```

### Step 2: Create Dashboard Callback Function
**New file**: `apps/core/dashboard.py`

This function will:
1. Query database for all statistics
2. Use `select_related`/`prefetch_related` for optimization
3. Return context dictionary for template

```python
from django.db.models import Count, Sum, F, Q
from apps.orders.models import Order, OrderItem, OrderStatusChoices
from apps.users.models import Customer
from apps.products.models import Product, ProductStatusChoices, ProductAvailabilityChoices
from django.utils import timezone
from datetime import timedelta

def dashboard_callback(request, context):
    """Prepare dashboard statistics for admin index page."""
    
    # Time ranges
    today = timezone.now().date()
    week_ago = today - timedelta(days=7)
    month_ago = today - timedelta(days=30)
    
    # Order statistics
    orders = Order.objects.all()
    total_orders = orders.count()
    new_orders = orders.filter(status=OrderStatusChoices.NEW).count()
    
    # Revenue calculation (from confirmed/completed orders)
    # Sum of all order items for non-cancelled orders
    revenue_orders = orders.filter(
        status__in=[OrderStatusChoices.CONFIRMED, OrderStatusChoices.COMPLETED]
    )
    total_revenue = sum(order.total_amount for order in revenue_orders)
    
    # Orders by status
    orders_by_status = orders.values('status').annotate(count=Count('id'))
    
    # Recent orders (last 10)
    recent_orders = orders.select_related('customer').prefetch_related('items')[:10]
    
    # Orders awaiting processing (new status)
    awaiting_orders = orders.filter(status=OrderStatusChoices.NEW).select_related('customer')[:5]
    
    # Customer statistics
    total_customers = Customer.objects.filter(is_active=True).count()
    new_customers_week = Customer.objects.filter(
        created_at__date__gte=week_ago, is_active=True
    ).count()
    recent_customers = Customer.objects.filter(is_active=True).order_by('-created_at')[:5]
    
    # Product statistics
    products = Product.objects.all()
    total_products = products.count()
    published_products = products.filter(status=ProductStatusChoices.PUBLISHED).count()
    
    products_by_status = products.values('status').annotate(count=Count('id'))
    products_by_availability = products.values('availability').annotate(count=Count('id'))
    
    # Products without images
    products_without_images = products.filter(images__isnull=True).count()
    
    context.update({
        # KPIs
        'total_orders': total_orders,
        'new_orders': new_orders,
        'total_revenue': total_revenue,
        'total_customers': total_customers,
        'published_products': published_products,
        
        # Breakdowns
        'orders_by_status': orders_by_status,
        'products_by_status': products_by_status,
        'products_by_availability': products_by_availability,
        
        # Lists
        'recent_orders': recent_orders,
        'awaiting_orders': awaiting_orders,
        'recent_customers': recent_customers,
        
        # Additional metrics
        'new_customers_week': new_customers_week,
        'products_without_images': products_without_images,
        'total_products': total_products,
    })
    
    return context
```

### Step 3: Configure Unfold Settings
**File**: `instrument_shop/settings.py`

Add `DASHBOARD_CALLBACK` to `UNFOLD` configuration:

```python
UNFOLD = {
    "DASHBOARD_CALLBACK": "apps.core.dashboard.dashboard_callback",
    # ... other settings
}
```

### Step 4: Create Dashboard Template
**New file**: `templates/admin/index.html`

Use Unfold's component system with Tailwind CSS classes. Template structure:

```html
{% extends "admin/index.html" %}
{% load i18n %}

{% block content %}
    {{ block.super }}
    
    <div class="p-6 space-y-6">
        <!-- KPI Cards Row -->
        <div class="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-5 gap-4">
            <!-- Total Orders -->
            <div class="bg-white dark:bg-base-800 rounded-lg shadow p-4">
                <div class="text-sm text-gray-500">Всего заказов</div>
                <div class="text-2xl font-bold">{{ total_orders }}</div>
            </div>
            
            <!-- New Orders (action required) -->
            <div class="bg-white dark:bg-base-800 rounded-lg shadow p-4 border-l-4 border-yellow-500">
                <div class="text-sm text-gray-500">Новые заказы</div>
                <div class="text-2xl font-bold text-yellow-600">{{ new_orders }}</div>
            </div>
            
            <!-- Total Revenue -->
            <div class="bg-white dark:bg-base-800 rounded-lg shadow p-4">
                <div class="text-sm text-gray-500">Выручка</div>
                <div class="text-2xl font-bold">{{ total_revenue }} ₽</div>
            </div>
            
            <!-- Total Customers -->
            <div class="bg-white dark:bg-base-800 rounded-lg shadow p-4">
                <div class="text-sm text-gray-500">Клиенты</div>
                <div class="text-2xl font-bold">{{ total_customers }}</div>
            </div>
            
            <!-- Published Products -->
            <div class="bg-white dark:bg-base-800 rounded-lg shadow p-4">
                <div class="text-sm text-gray-500">Товары в каталоге</div>
                <div class="text-2xl font-bold">{{ published_products }}</div>
            </div>
        </div>
        
        <!-- Second Row: Lists -->
        <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <!-- Orders Awaiting Processing -->
            <div class="bg-white dark:bg-base-800 rounded-lg shadow">
                <div class="p-4 border-b">
                    <h3 class="text-lg font-semibold">Заказы к обработке</h3>
                </div>
                <div class="p-4">
                    {% if awaiting_orders %}
                        <table class="w-full">
                            {% for order in awaiting_orders %}
                                <tr class="border-b">
                                    <td><a href="/admin/orders/order/{{ order.pk }}/change/">#{{ order.pk }}</a></td>
                                    <td>{{ order.customer.email }}</td>
                                    <td>{{ order.created_at|date:"d.m.Y H:i" }}</td>
                                    <td>{{ order.total_amount }} ₽</td>
                                </tr>
                            {% endfor %}
                        </table>
                    {% else %}
                        <p class="text-gray-500">Нет новых заказов</p>
                    {% endif %}
                </div>
            </div>
            
            <!-- Recent Orders -->
            <div class="bg-white dark:bg-base-800 rounded-lg shadow">
                <div class="p-4 border-b">
                    <h3 class="text-lg font-semibold">Последние заказы</h3>
                </div>
                <div class="p-4">
                    {% if recent_orders %}
                        <table class="w-full">
                            <tr>
                                <th>ID</th>
                                <th>Клиент</th>
                                <th>Статус</th>
                                <th>Сумма</th>
                            </tr>
                            {% for order in recent_orders %}
                                <tr class="border-b">
                                    <td><a href="/admin/orders/order/{{ order.pk }}/change/">#{{ order.pk }}</a></td>
                                    <td>{{ order.customer.email }}</td>
                                    <td>{{ order.get_status_display }}</td>
                                    <td>{{ order.total_amount }} ₽</td>
                                </tr>
                            {% endfor %}
                        </table>
                    {% else %}
                        <p class="text-gray-500">Заказов пока нет</p>
                    {% endif %}
                </div>
            </div>
        </div>
        
        <!-- Third Row: Status Breakdowns -->
        <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <!-- Order Status Breakdown -->
            <div class="bg-white dark:bg-base-800 rounded-lg shadow p-4">
                <h3 class="text-lg font-semibold mb-4">Статусы заказов</h3>
                {% for status_item in orders_by_status %}
                    <div class="flex justify-between py-2 border-b">
                        <span>{{ status_item.status }}</span>
                        <span class="font-bold">{{ status_item.count }}</span>
                    </div>
                {% endfor %}
            </div>
            
            <!-- Product Status Breakdown -->
            <div class="bg-white dark:bg-base-800 rounded-lg shadow p-4">
                <h3 class="text-lg font-semibold mb-4">Статусы товаров</h3>
                {% for status_item in products_by_status %}
                    <div class="flex justify-between py-2 border-b">
                        <span>{{ status_item.status }}</span>
                        <span class="font-bold">{{ status_item.count }}</span>
                    </div>
                {% endfor %}
                
                <h3 class="text-lg font-semibold mb-4 mt-6">Наличие товаров</h3>
                {% for avail_item in products_by_availability %}
                    <div class="flex justify-between py-2 border-b">
                        <span>{{ avail_item.availability }}</span>
                        <span class="font-bold">{{ avail_item.count }}</span>
                    </div>
                {% endfor %}
            </div>
        </div>
    </div>
{% endblock %}
```

### Step 5: Create Required Directories
```bash
mkdir -p templates/admin
mkdir -p apps/core  # if not exists
touch apps/core/__init__.py  # if not exists
```

## Files to Modify/Create

### New Files:
1. `templates/admin/index.html` - Dashboard template
2. `apps/core/dashboard.py` - Dashboard callback function
3. `apps/core/__init__.py` - Package file (if not exists)

### Modified Files:
1. `instrument_shop/settings.py`:
   - Add `BASE_DIR / "templates"` to `TEMPLATES[0]['DIRS']`
   - Add `DASHBOARD_CALLBACK` to `UNFOLD` dict

## Optimization Considerations

1. **Database Queries**: Use `select_related` and `prefetch_related` in dashboard callback
2. **Caching**: For high-traffic sites, consider caching dashboard data (not needed for MVP)
3. **Query Efficiency**: 
   - Use `Count()`, `Sum()` aggregations instead of Python loops where possible
   - For `total_revenue`, use database-level aggregation

## Improved Revenue Calculation (if needed)
Instead of Python loop:
```python
from django.db.models import Sum, F

total_revenue = OrderItem.objects.filter(
    order__status__in=[OrderStatusChoices.CONFIRMED, OrderStatusChoices.COMPLETED]
).aggregate(
    total=Sum(F('quantity') * F('unit_price'))
)['total'] or 0
```

## Completion Criteria

1. ✅ Dashboard callback configured in `settings.py`
2. ✅ Template `templates/admin/index.html` created with:
   - KPI cards (orders, revenue, customers, products)
   - Recent orders table
   - Orders awaiting processing table
   - Status breakdowns (orders and products)
3. ✅ Dashboard displays correctly when accessing `/admin/`
4. ✅ All statistics are accurate and up-to-date
5. ✅ Template uses Unfold-compatible HTML/Tailwind classes
6. ✅ Dashboard is mobile-responsive (via Tailwind grid classes)

## Priority
Medium - UX improvement for administrators

## Dependencies
- Task 13 (Admin Panel Russian Localization) - ✅ Completed
- Unfold admin theme - ✅ Installed and configured

"""
Dashboard callback for Unfold admin interface.

Provides statistics and KPIs for the admin dashboard.
"""
from datetime import timedelta
from decimal import Decimal

from django.db.models import (
    Avg,
    Count,
    F,
    OuterRef,
    Q,
    Subquery,
    Sum,
)
from django.db.models.functions import TruncMonth
from django.utils import timezone

from apps.favorites.models import Favorite
from apps.feedback.models import FeedbackMessage
from apps.news.models import NewsArticle, NewsArticleStatus
from apps.orders.models import Order, OrderItem, OrderStatusChoices
from apps.products.models import (
    Category,
    Product,
    ProductAvailabilityChoices,
    ProductStatusChoices,
)
from apps.reviews.models import Review
from apps.users.models import Customer


REVENUE_STATUSES = [OrderStatusChoices.CONFIRMED, OrderStatusChoices.COMPLETED]


def dashboard_callback(request, context):
    """Prepare dashboard statistics for the admin index page."""
    now = timezone.now()
    week_ago = now - timedelta(days=7)
    month_ago = now - timedelta(days=30)

    # ====================
    # Order Statistics
    # ====================
    orders = Order.objects.all()
    total_orders = orders.count()
    new_orders = orders.filter(status=OrderStatusChoices.NEW).count()

    revenue_items_qs = OrderItem.objects.filter(order__status__in=REVENUE_STATUSES)
    total_revenue = revenue_items_qs.aggregate(
        total=Sum(F("quantity") * F("unit_price"))
    )["total"] or Decimal("0.00")

    # AOV — средний чек по подтверждённым/выполненным заказам
    paid_orders_qs = orders.filter(status__in=REVENUE_STATUSES)
    paid_orders_count = paid_orders_qs.count()
    aov = (total_revenue / paid_orders_count) if paid_orders_count else Decimal("0.00")

    orders_by_status = orders.values("status").annotate(count=Count("id")).order_by("status")

    recent_orders = orders.select_related("customer").prefetch_related("items")[:10]
    awaiting_orders = (
        orders.filter(status=OrderStatusChoices.NEW)
        .select_related("customer")
        .prefetch_related("items")[:5]
    )

    # ====================
    # Customer Statistics
    # ====================
    total_customers = Customer.objects.filter(is_active=True).count()
    new_customers_week = Customer.objects.filter(
        created_at__gte=week_ago,
        is_active=True,
    ).count()
    recent_customers = Customer.objects.filter(is_active=True).order_by("-created_at")[:5]

    # ====================
    # Product Statistics
    # ====================
    products = Product.objects.all()
    total_products = products.count()
    published_products = products.filter(status=ProductStatusChoices.PUBLISHED).count()

    products_by_status = (
        products.values("status").annotate(count=Count("id")).order_by("status")
    )
    products_by_availability = (
        products.values("availability").annotate(count=Count("id")).order_by("availability")
    )

    products_without_images = products.filter(images__isnull=True).distinct().count()
    products_without_categories = products.filter(categories__isnull=True).distinct().count()

    # ====================
    # Period Metrics (last 30 days)
    # ====================
    orders_last_30d = orders.filter(created_at__gte=month_ago).count()
    revenue_last_30d = (
        OrderItem.objects.filter(
            order__status__in=REVENUE_STATUSES,
            order__created_at__gte=month_ago,
        ).aggregate(total=Sum(F("quantity") * F("unit_price")))["total"]
        or Decimal("0.00")
    )

    # ====================
    # Chart Data: Monthly Sales Revenue
    # ====================
    monthly_sales = (
        Order.objects.filter(status__in=REVENUE_STATUSES)
        .annotate(month=TruncMonth("created_at"))
        .values("month")
        .annotate(total=Sum(F("items__quantity") * F("items__unit_price")))
        .order_by("month")
    )
    monthly_sales_labels = [item["month"].strftime("%B %Y") for item in monthly_sales]
    monthly_sales_data = [float(item["total"] or 0) for item in monthly_sales]

    # ====================
    # Chart Data: Sales by Category
    # Используем "первичную" категорию (первая по алфавиту) для каждого товара,
    # чтобы избежать двойного счёта при M2M (товар в нескольких категориях).
    # ====================
    primary_cat_subquery = (
        Category.objects.filter(products=OuterRef("product"))
        .order_by("name")
        .values("name")[:1]
    )
    sales_by_category = (
        OrderItem.objects.filter(order__status__in=REVENUE_STATUSES)
        .annotate(category_name=Subquery(primary_cat_subquery))
        .values("category_name")
        .annotate(total=Sum(F("quantity") * F("unit_price")))
        .order_by("-total")[:10]
    )
    category_labels = [
        item["category_name"] or "Без категории" for item in sales_by_category
    ]
    category_data = [float(item["total"] or 0) for item in sales_by_category]

    # ====================
    # Chart Data: Order Status Distribution
    # ====================
    status_distribution = list(orders.values("status").annotate(count=Count("id")))
    status_colors_map = {
        "new": "rgb(234, 179, 8)",
        "processing": "rgb(59, 130, 246)",
        "confirmed": "rgb(34, 197, 94)",
        "completed": "rgb(107, 114, 128)",
        "cancelled": "rgb(239, 68, 68)",
    }
    status_choices_map = dict(OrderStatusChoices.choices)
    status_labels = [status_choices_map.get(item["status"], item["status"]) for item in status_distribution]
    status_data = [item["count"] for item in status_distribution]
    status_colors = [
        status_colors_map.get(item["status"], "rgb(156, 163, 175)") for item in status_distribution
    ]

    # ====================
    # Feedback (обратная связь)
    # ====================
    feedback_qs = FeedbackMessage.objects.all()
    feedback_unprocessed = feedback_qs.filter(processed_at__isnull=True).count()
    feedback_total = feedback_qs.count()
    feedback_last_week = feedback_qs.filter(created_at__gte=week_ago).count()
    recent_feedback = feedback_qs.filter(processed_at__isnull=True).order_by("-created_at")[:5]

    # ====================
    # Favorites (топ-товаров по добавлениям)
    # ====================
    favorites_total = Favorite.objects.count()
    top_favorited = (
        Product.objects.annotate(fav_count=Count("favorited_by"))
        .filter(fav_count__gt=0)
        .order_by("-fav_count")[:5]
    )

    # ====================
    # News (контент-метрики)
    # ====================
    news_qs = NewsArticle.objects.all()
    news_published = news_qs.filter(status=NewsArticleStatus.PUBLISHED).count()
    news_drafts = news_qs.filter(status=NewsArticleStatus.DRAFT).count()
    recent_news = (
        news_qs.filter(status=NewsArticleStatus.PUBLISHED)
        .order_by("-date")[:5]
    )

    # ====================
    # Reviews (модерация и качество)
    # ====================
    reviews_qs = Review.objects.all()
    reviews_total = reviews_qs.count()
    reviews_published = reviews_qs.filter(is_published=True).count()
    reviews_hidden = reviews_qs.filter(is_published=False).count()
    reviews_avg_grade = reviews_qs.filter(is_published=True).aggregate(avg=Avg("grade"))["avg"] or 0
    reviews_by_grade_qs = (
        reviews_qs.filter(is_published=True)
        .values("grade")
        .annotate(count=Count("id"))
        .order_by("-grade")
    )
    # Заполнить отсутствующие оценки нулями, чтобы шаблон всегда показывал 5..1
    grade_counts = {item["grade"]: item["count"] for item in reviews_by_grade_qs}
    reviews_by_grade = [
        {"grade": g, "count": grade_counts.get(g, 0)} for g in range(5, 0, -1)
    ]

    # ====================
    # Top selling products (по выручке за всё время)
    # ====================
    top_products = (
        OrderItem.objects.filter(order__status__in=REVENUE_STATUSES)
        .values("product_id", "product_name")
        .annotate(
            revenue=Sum(F("quantity") * F("unit_price")),
            sold_qty=Sum("quantity"),
        )
        .order_by("-revenue")[:10]
    )

    context.update(
        {
            # KPI Cards
            "total_orders": total_orders,
            "new_orders": new_orders,
            "total_revenue": total_revenue,
            "total_customers": total_customers,
            "published_products": published_products,
            "total_products": total_products,
            "aov": aov,
            "paid_orders_count": paid_orders_count,
            # Action-required KPI
            "feedback_unprocessed": feedback_unprocessed,
            # Breakdowns
            "orders_by_status": orders_by_status,
            "products_by_status": products_by_status,
            "products_by_availability": products_by_availability,
            # Lists (actionable items)
            "recent_orders": recent_orders,
            "awaiting_orders": awaiting_orders,
            "recent_customers": recent_customers,
            "recent_feedback": recent_feedback,
            # Additional metrics
            "new_customers_week": new_customers_week,
            "products_without_images": products_without_images,
            "products_without_categories": products_without_categories,
            "orders_last_30d": orders_last_30d,
            "revenue_last_30d": revenue_last_30d,
            # Chart Data
            "monthly_sales_labels": monthly_sales_labels,
            "monthly_sales_data": monthly_sales_data,
            "category_labels": category_labels,
            "category_data": category_data,
            "status_labels": status_labels,
            "status_data": status_data,
            "status_colors": status_colors,
            # Feedback
            "feedback_total": feedback_total,
            "feedback_last_week": feedback_last_week,
            # Favorites
            "favorites_total": favorites_total,
            "top_favorited": top_favorited,
            # News
            "news_published": news_published,
            "news_drafts": news_drafts,
            "recent_news": recent_news,
            # Reviews
            "reviews_total": reviews_total,
            "reviews_published": reviews_published,
            "reviews_hidden": reviews_hidden,
            "reviews_avg_grade": reviews_avg_grade,
            "reviews_by_grade": reviews_by_grade,
            # Top selling products
            "top_products": top_products,
        }
    )

    return context

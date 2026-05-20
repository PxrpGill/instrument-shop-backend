from ninja import NinjaAPI

from apps.orders.controllers import router as orders_router
from apps.pages.controllers import router as pages_router
from apps.products.catalog_controllers import router as catalog_router
from apps.products.controllers import categories_router, images_router
from apps.products.controllers import router as products_router
from apps.shared.exception_handlers import register_error_handlers
from apps.users.api.auth_controllers import router as auth_router
from apps.users.api.role_controllers import router as admin_router

api = NinjaAPI(
    title="Instrument Shop API",
    version="1.0.0",
    description="REST API для интернет-магазина строительных инструментов",
)

register_error_handlers(api)

# Аутентификация по контракту contracts/auth/* (UUID id, JWT + refresh)
api.add_router("/auth/", auth_router)

# Admin-only role management endpoints
api.add_router("/v1/admin/", admin_router)

# Products and categories
api.add_router("/v1/products/", products_router)
api.add_router("/v1/categories/", categories_router)
api.add_router("/v1/products/", images_router)

# Orders
api.add_router("/v1/orders/", orders_router)

# Public storefront catalog (contracts/catalog/*)
api.add_router("/catalog", catalog_router)

# Pages (public content) — см. contracts/pages/*
api.add_router("/pages/", pages_router)


@api.get("/hello")
def hello(request):
    return {"message": "Hello from Django Ninja!"}

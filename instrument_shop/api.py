from ninja import NinjaAPI

from apps.products.controllers import categories_router, images_router
from apps.products.controllers import router as products_router
from apps.products.public_api import public_router
from apps.users.api.controllers import router as customers_router
from apps.users.api.role_controllers import router as admin_router
from apps.orders.controllers import router as orders_router

api = NinjaAPI(
    title="Instrument Shop API",
    version="1.0.0",
    description="REST API для интернет-магазина строительных инструментов",
)

# Public/customer endpoints
api.add_router("/v1/customers/", customers_router)

# Admin-only role management endpoints
api.add_router("/v1/admin/", admin_router)

# Products and categories
api.add_router("/v1/products/", products_router)
api.add_router("/v1/categories/", categories_router)
api.add_router("/v1/products/", images_router)

# Orders
api.add_router("/v1/orders/", orders_router)

# Public storefront endpoints (no auth required)
api.add_router("/v1/public/", public_router)


@api.get("/hello")
def hello(request):
    return {"message": "Hello from Django Ninja!"}

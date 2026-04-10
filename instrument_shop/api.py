from ninja import NinjaAPI

from apps.users.api.controllers import router as customers_router
from apps.products.controllers import router as products_router
from apps.products.controllers import categories_router
from apps.products.controllers import images_router

api = NinjaAPI(
    title="Instrument Shop API",
    version="1.0.0",
    description="REST API для интернет-магазина музыкальных инструментов",
)

api.add_router('/v1/customers/', customers_router)
api.add_router('/v1/categories/', categories_router)
api.add_router('/v1/products/', products_router)
api.add_router('/v1/products/', images_router)


@api.get("/hello")
def hello(request):
    return {"message": "Hello from Django Ninja!"}
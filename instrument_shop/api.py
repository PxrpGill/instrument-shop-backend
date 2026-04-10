from ninja import NinjaAPI

from apps.products.controllers import router as products_router
from apps.products.controllers import categories_router
from apps.products.controllers import images_router

api = NinjaAPI(
    title="Instrument Shop API",
    version="1.0.0",
    description="REST API для интернет-магазина музыкальных инструментов",
)

api.add_router('/categories/', categories_router)
api.add_router('/products/', products_router)
api.add_router('/products/', images_router)


@api.get("/hello")
def hello(request):
    return {"message": "Hello from Django Ninja!"}
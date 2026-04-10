from ninja import NinjaAPI

from apps.products.controllers import router as products_router

api = NinjaAPI(
    title="Instrument Shop API",
    version="1.0.0",
    description="REST API для интернет-магазина музыкальных инструментов",
)

api.add_router('/products/', products_router)


@api.get("/hello")
def hello(request):
    return {"message": "Hello from Django Ninja!"}
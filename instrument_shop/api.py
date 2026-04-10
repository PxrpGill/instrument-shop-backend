from ninja import NinjaAPI

from apps.products.controllers import router as products_router

api = NinjaAPI()

api.add_router('/products/', products_router)


@api.get("/hello")
def hello(request):
    return {"message": "Hello from Django Ninja!"}
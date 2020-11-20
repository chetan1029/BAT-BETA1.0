from django.urls import include, path
from rest_framework_nested import routers

from bat.company.urls import router
from bat.product.views.component import ProductParentViewSet, ProductViewSet

product_parent_router = routers.NestedSimpleRouter(
    router, "companies", lookup="company"
)
product_parent_router.register(
    "product_parent", ProductParentViewSet, basename="company-product_parent"
)


product_router = routers.NestedSimpleRouter(
    router, "companies", lookup="company"
)
product_router.register(
    "products", ProductViewSet, basename="company-product"
)


app_name = "product"

urlpatterns = [
    path("", include(product_parent_router.urls)),
    path("", include(product_router.urls)),
]
